from django.core.exceptions import FieldError

from .constants import *

import django_mock_queries.query


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


# noinspection PyProtectedMember
def find_field_names(obj):
    field_names = set()
    field_names.update(obj._meta._forward_fields_map.keys())
    field_names.update(field.get_accessor_name()
                       for field in obj._meta.fields_map.values())
    for parent in obj._meta.parents.keys():
        parent_fields = find_field_names(parent) or []
        field_names.update(parent_fields)
    return sorted(field_names)


def get_attribute(obj, attr, default=None):
    result = obj
    comparison = None
    parts = attr.split('__')

    for p in parts:
        if p in COMPARISONS:
            comparison = p
        elif result is None:
            break
        else:
            field_names = find_field_names(result)
            if p != 'pk' and field_names and p not in field_names:
                message = "Cannot resolve keyword '{}' into field. Choices are {}.".format(
                    p,
                    ', '.join(map(repr, map(str, field_names)))
                )
                raise FieldError(message)
            result = getattr(result, p, None)

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
