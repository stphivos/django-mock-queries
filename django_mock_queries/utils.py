from .constants import *


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


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
