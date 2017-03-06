from django.core.exceptions import FieldError
from mock import Mock

from .constants import *
from .exceptions import *

import django_mock_queries.query


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


# noinspection PyProtectedMember
def find_field_names(obj, **kwargs):
    def names(field):
        name = field.get_accessor_name()
        model_name = field.related_model._meta.model_name.lower()

        if kwargs.get('related_set_singular', False) and name[-4:] == '_set':
            return {model_name: name}
        else:
            return {name: name}

    if not hasattr(obj, '_meta'):
        # It is possibly a MockSet.
        use_obj = getattr(obj, 'model', None)

        # Make it easier for MockSet, but Django's QuerySet will always have a model.
        if not use_obj and is_list_like_iter(obj) and len(obj) > 0:
            return find_field_names(obj[0], **kwargs)

    field_names = {}

    if hasattr(obj, '_meta'):
        field_names.update({key: key for key in obj._meta._forward_fields_map.keys()})
        [field_names.update(names(field)) for field in obj._meta.fields_map.values()]

        for parent in obj._meta.parents.keys():
            field_names.update({key: key for key in find_field_names(parent)[0]})

    return list(field_names.keys()), list(field_names.values())


def get_attribute(obj, attr, default=None, **kwargs):
    result = obj
    comparison = None
    parts = attr.split('__')

    for nested_field in parts:
        if nested_field in COMPARISONS:
            comparison = nested_field
        elif result is None:
            break
        else:
            lookup_fields, target_fields = find_field_names(result, **kwargs)

            if nested_field != 'pk' and lookup_fields and nested_field not in lookup_fields:
                message = "Cannot resolve keyword '{}' into field. Choices are {}.".format(
                    nested_field,
                    ', '.join(map(repr, map(str, sorted(lookup_fields))))
                )
                raise FieldError(message)

            if nested_field in lookup_fields:
                target_field = target_fields[lookup_fields.index(nested_field)]
            else:
                target_field = nested_field

            if is_list_like_iter(result):
                result = [get_attribute(x, target_field)[0] for x in result]
            else:
                result = getattr(result, target_field, None)

    value = result if result is not None else default
    return value, comparison


def is_match(first, second, comparison=None):
    if isinstance(first, django_mock_queries.query.MockBase):
        return is_match_in_children(comparison, first, second)
    if (isinstance(first, (int, str)) and
            isinstance(second, django_mock_queries.query.MockBase)):
        second = convert_to_pks(second)
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
    }[comparison]()


def convert_to_pks(query):
    return [item.pk for item in query]


def is_match_in_children(comparison, first, second):
    return any(is_match(item, second, comparison)
               for item in first)


def matches(*source, **attrs):
    exclude = []
    for x in source:
        for attr_name, filter_value in attrs.items():
            attr_value, comparison = get_attribute(x, attr_name)
            if not is_match(attr_value, filter_value, comparison):
                exclude.append(x)
                break
    for x in source:
        if x not in exclude:
            yield x


def validate_mock_set(mock_set):
    if mock_set.model is None:
        raise ModelNotSpecified()


def is_list_like_iter(obj):
    if isinstance(obj, django_mock_queries.query.MockModel):
        return False
    elif isinstance(obj, django_mock_queries.query.MockBase):
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
