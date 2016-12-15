from django.core.exceptions import FieldError

from .constants import *


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


# noinspection PyProtectedMember
def find_field_names(obj):
    field_names = set()
    field_names.update(obj._meta._forward_fields_map.keys())
    field_names.update(obj._meta.fields_map.keys())
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
        COMPARISON_ISNULL: lambda: (first is None) == bool(second),
    }[comparison]()


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
