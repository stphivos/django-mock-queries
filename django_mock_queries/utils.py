from datetime import datetime, date
from django.core.exceptions import FieldError
from django.db.models import F, Value, Case
from django.db.models.functions import Coalesce
from unittest.mock import Mock

from .comparisons import *
from .constants import *
from .exceptions import *

import django_mock_queries.query


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


def find_field_names_from_meta(meta, annotated=None, **kwargs):
    field_names = {}
    annotated = annotated or []
    concrete_only = kwargs.get('concrete_only', False)

    if concrete_only:
        fields_no_mapping = [f.attname for f in meta.concrete_fields] + annotated
        fields_with_mapping = []
    else:
        fields_no_mapping = [f for f in meta._forward_fields_map.keys()] + annotated
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
        lookup_fields, actual_fields = find_field_names_from_meta(
            obj._meta,
            annotated=getattr(obj, '_annotated_fields', []),
            **kwargs
        )
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
    elif is_like_date_or_datetime(obj):
        return obj
    else:
        return getattr(obj, field_name, default)


def get_attribute(obj, attr, default=None):
    result = obj
    comparison = None
    if isinstance(attr, F):
        attr = attr.deconstruct()[1][0]
    elif isinstance(attr, Value):
        return attr.value, None
    elif isinstance(attr, Case):
        for case in attr.cases:
            if filter_results([obj], case.condition):
                return get_attribute(obj, case.result)
        else:
            return get_attribute(obj, attr.default)
    elif isinstance(attr, Coalesce):
        for expr in attr.source_expressions:
            res, comp = get_attribute(obj, expr)
            if res is not None:
                return res, comp
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
    if (isinstance(first, (int, str)) and isinstance(second, django_mock_queries.query.MockSet)):
        second = convert_to_pks(second)
    if (isinstance(first, date) or isinstance(first, datetime)) \
            and isinstance(comparison, tuple) and len(comparison) == 2:
        first = extract(first, comparison[0])
        comparison = comparison[1]
    if not comparison:
        return first == second
    return {
        COMPARISON_EXACT: exact_comparison,
        COMPARISON_IEXACT: iexact_comparison,
        COMPARISON_CONTAINS: contains_comparison,
        COMPARISON_ICONTAINS: icontains_comparison,
        COMPARISON_GT: gt_comparison,
        COMPARISON_GTE: gte_comparison,
        COMPARISON_LT: lt_comparison,
        COMPARISON_LTE: lte_comparison,
        COMPARISON_IN: in_comparison,
        COMPARISON_STARTSWITH: startswith_comparison,
        COMPARISON_ISTARTSWITH: istartswith_comparison,
        COMPARISON_ENDSWITH: endswith_comparison,
        COMPARISON_IENDSWITH: iendswith_comparison,
        COMPARISON_ISNULL: isnull_comparison,
        COMPARISON_REGEX: regex_comparison,
        COMPARISON_IREGEX: iregex_comparison,
        COMPARISON_RANGE: range_comparison,
        COMPARISON_OVERLAP: overlap_comparison,
    }[comparison](first, second)


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


def is_like_date_or_datetime(obj):
    return type(obj) in [date, datetime]


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


def filter_results(source, query):
    results = []

    for child in query.children:
        filtered = _filter_single_q(source, child, query.negated)

        if filtered:
            if not results or query.connector == CONNECTORS_OR:
                results = merge(results, filtered)
            else:
                results = intersect(results, filtered)
        elif query.connector == CONNECTORS_AND:
            return []

    return results


def _filter_single_q(source, q_obj, negated):
    if isinstance(q_obj, DjangoQ):
        return filter_results(source, q_obj)
    else:
        return matches(negated=negated, *source, **{q_obj[0]: q_obj[1]})


def get_nested_attr(obj, attr_path, default=None):
    attrs = attr_path.split('.')
    try:
        for attr in attrs:
            obj = getattr(obj, attr)
        return obj
    except AttributeError:
        return default
