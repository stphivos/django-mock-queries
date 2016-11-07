from .constants import *


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


def get_attribute(obj, attr, default=None):
    result = obj
    lookup = '__'
    parts = attr.split(lookup)
    comparison = parts[-1] if lookup in attr and parts[-1] in COMPARISONS else None

    for p in parts:
        if result is None or p == comparison:
            break
        elif not hasattr(result, p):
            raise TypeError('Related Field got invalid lookup: {}'.format(p))
        else:
            result = getattr(result, p)

    value = default if result is None else result
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
