from datetime import datetime, date
from django.core.exceptions import FieldError
from mock import Mock

from .constants import *
from .exceptions import *

import django_mock_queries.query
import re


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


def get_field_mapping(field):
    name = field.get_accessor_name()
    model_name = field.related_model._meta.model_name.lower()

    if name[-4:] == '_set':
        return {model_name: name}
    else:
        return {name: name}


def find_field_names_from_meta(meta, **kwargs):
    field_names = {}
    concrete_only = kwargs.get('concrete_only', False)

    if concrete_only:
        fields_no_mapping = [f.attname for f in meta.concrete_fields]
        fields_with_mapping = []
    else:
        fields_no_mapping = [f for f in meta._forward_fields_map.keys()]
        fields_with_mapping = [f for f in meta.fields_map.values()]

        for parent in meta.parents.keys():
            fields_no_mapping.extend([key for key in find_field_names(parent)[0]])

    for field in fields_no_mapping:
        field_names[field] = field

    for field in fields_with_mapping:
        field_names.update(get_field_mapping(field))

    return list(field_names.keys()), list(field_names.values())


def find_field_names_from_obj(obj, **kwargs):
    lookup_fields, actual_fields = [], []

    if type(obj) is dict:
        lookup_fields = actual_fields = list(obj.keys())
    else:
        # It is possibly a MockSet.
        use_obj = getattr(obj, 'model', None)

        # Make it easier for MockSet, but Django's QuerySet will always have a model.
        if not use_obj and is_list_like_iter(obj) and len(obj) > 0:
            lookup_fields, actual_fields = find_field_names(obj[0], **kwargs)

    return lookup_fields, actual_fields


def find_field_names(obj, **kwargs):
    if hasattr(obj, '_meta'):
        lookup_fields, actual_fields = find_field_names_from_meta(obj._meta, **kwargs)
    else:
        lookup_fields, actual_fields = find_field_names_from_obj(obj, **kwargs)

    return lookup_fields, actual_fields


def validate_field(field_name, model_fields, for_update=False):
    if '__' in field_name and for_update:
        raise FieldError(
            'Cannot update model field %r (only non-relations and foreign keys permitted).' % field_name
        )
    if field_name != 'pk' and field_name not in model_fields:
        message = "Cannot resolve keyword '{}' into field. Choices are {}.".format(
            field_name,
            ', '.join(map(repr, map(str, sorted(model_fields))))
        )
        raise FieldError(message)


def get_field_value(obj, field_name, default=None):
    if type(obj) is dict:
        return obj.get(field_name, default)
    elif is_list_like_iter(obj):
        return [get_attribute(x, field_name, default)[0] for x in obj]
    else:
        return getattr(obj, field_name, default)


def get_attribute(obj, attr, default=None):
    result = obj
    comparison = None
    parts = attr.split('__')

    for i, attr_part in enumerate(parts):
        if attr_part in COMPARISONS:
            comparison = attr_part
        elif attr_part in DATETIME_COMPARISONS and type(result) in [date, datetime]:
            comparison_type = parts[i + 1] if i + 1 < len(parts) else COMPARISON_EXACT
            comparison = (attr_part, comparison_type)
            break
        elif result is None:
            result = default
            break
        else:
            lookup_fields, actual_fields = find_field_names(result)

            if lookup_fields:
                validate_field(attr_part, lookup_fields)

            field = actual_fields[lookup_fields.index(attr_part)] if attr_part in lookup_fields else attr_part
            result = get_field_value(result, field, default)
    return result, comparison


def is_match(first, second, comparison=None):
    if isinstance(first, django_mock_queries.query.MockSet):
        return is_match_in_children(comparison, first, second)
    if (isinstance(first, (int, str)) and
            isinstance(second, django_mock_queries.query.MockSet)):
        second = convert_to_pks(second)
    if (isinstance(first, date) or isinstance(first, datetime)) \
            and isinstance(comparison, tuple) and len(comparison) == 2:
        first = extract(first, comparison[0])
        comparison = comparison[1]
    if not comparison:
        return first == second
    return {
        COMPARISON_EXACT: lambda: first == second,
        COMPARISON_IEXACT: lambda: first.lower() == second.lower(),
        COMPARISON_CONTAINS: lambda: second in first,
        COMPARISON_ICONTAINS: lambda: second.lower() in first.lower(),
        COMPARISON_GT: lambda: first > second,
        COMPARISON_GTE: lambda: first >= second,
        COMPARISON_LT: lambda: first < second,
        COMPARISON_LTE: lambda: first <= second,
        COMPARISON_IN: lambda: first in second,
        COMPARISON_STARTSWITH: lambda: first.startswith(second),
        COMPARISON_ISTARTSWITH: lambda: first.lower().startswith(second.lower()),
        COMPARISON_ENDSWITH: lambda: first.endswith(second),
        COMPARISON_IENDSWITH: lambda: first.lower().endswith(second.lower()),
        COMPARISON_ISNULL: lambda: (first is None) == bool(second),
        COMPARISON_REGEX: lambda: re.search(second, first) is not None,
        COMPARISON_IREGEX: lambda: re.search(second, first, flags=re.I) is not None,
        COMPARISON_RANGE: lambda: second[0] <= first <= second[1]
    }[comparison]()


def extract(obj, comparison):
    result_dict = None
    if isinstance(obj, date):
        result_dict = {
            COMPARISON_DATE: obj,
            COMPARISON_YEAR: obj.year,
            COMPARISON_MONTH: obj.month,
            COMPARISON_DAY: obj.day,
            COMPARISON_WEEK_DAY: (obj.weekday() + 1) % 7 + 1,
        }
    if isinstance(obj, datetime):
        result_dict = {
            COMPARISON_DATE: obj.date(),
            COMPARISON_YEAR: obj.year,
            COMPARISON_MONTH: obj.month,
            COMPARISON_DAY: obj.day,
            COMPARISON_WEEK_DAY: (obj.weekday() + 1) % 7 + 1,
            COMPARISON_HOUR: obj.hour,
            COMPARISON_MINUTE: obj.minute,
            COMPARISON_SECOND: obj.second,
        }
    return result_dict[comparison]


def convert_to_pks(query):
    try:
        return [item.pk for item in query]
    except AttributeError:
        return query  # Didn't have pk's, keep original items


def is_match_in_children(comparison, first, second):
    return any(is_match(item, second, comparison)
               for item in first)


def is_disqualified(obj, attrs, negated):
    for attr_name, filter_value in attrs.items():
        attr_value, comparison = get_attribute(obj, attr_name)
        match = is_match(attr_value, filter_value, comparison)

        if (match and negated) or (not match and not negated):
            return True

    return False


def matches(*source, **attrs):
    negated = attrs.pop('negated', False)
    disqualified = [x for x in source if is_disqualified(x, attrs, negated)]

    return [x for x in source if x not in disqualified]


def validate_mock_set(mock_set, for_update=False, **fields):
    if mock_set.model is None:
        raise ModelNotSpecified()

    _, actual_fields = find_field_names(mock_set.model)

    for k in fields.keys():
        validate_field(k, actual_fields, for_update)


def validate_date_or_datetime(value, comparison):
    mapping = {
        COMPARISON_YEAR: lambda: True,
        COMPARISON_MONTH: lambda: MONTH_BOUNDS[0] <= value <= MONTH_BOUNDS[1],
        COMPARISON_DAY: lambda: DAY_BOUNDS[0] <= value <= DAY_BOUNDS[1],
        COMPARISON_WEEK_DAY: lambda: WEEK_DAY_BOUNDS[0] <= value <= WEEK_DAY_BOUNDS[1],
        COMPARISON_HOUR: lambda: HOUR_BOUNDS[0] <= value <= HOUR_BOUNDS[1],
        COMPARISON_MINUTE: lambda: MINUTE_BOUNDS[0] <= value <= MINUTE_BOUNDS[1],
        COMPARISON_SECOND: lambda: SECOND_BOUNDS[0] <= value <= SECOND_BOUNDS[1],
    }
    if not mapping[comparison]():
        raise ValueError('{} is incorrect value for {}'.format(value, comparison))


def is_list_like_iter(obj):
    if isinstance(obj, django_mock_queries.query.MockModel):
        return False
    elif isinstance(obj, django_mock_queries.query.MockSet):
        return True
    elif isinstance(obj, Mock):
        return False

    return hasattr(obj, '__iter__') and not isinstance(obj, str)


def flatten_list(source):
    target = []
    for x in source:
        if not is_list_like_iter(x):
            target.append(x)
        else:
            target.extend(flatten_list(x))
    return target


def truncate(obj, kind):
    trunc_mapping = None
    if isinstance(obj, date):
        trunc_mapping = {
            'year': obj.replace(month=1, day=1),
            'month': obj.replace(day=1),
            'day': obj
        }
    if isinstance(obj, datetime):
        trunc_mapping = {
            'year': obj.replace(month=1, day=1, hour=0, minute=0, second=0),
            'month': obj.replace(day=1, hour=0, minute=0, second=0),
            'day': obj.replace(hour=0, minute=0, second=0),
            'hour': obj.replace(minute=0, second=0),
            'minute': obj.replace(second=0),
            'second': obj
        }
    return trunc_mapping[kind]


def hash_dict(obj, *fields):
    field_names = fields or find_field_names(obj, concrete_only=True)[1]
    obj_values = {f: get_field_value(obj, f) for f in field_names}

    return hash(tuple(sorted((k, v) for k, v in obj_values.items() if not fields or k in fields)))
