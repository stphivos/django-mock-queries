import re


def exact_comparison(first, second):
    return first == second


def iexact_comparison(first, second):
    return first.lower() == second.lower()


def contains_comparison(first, second):
    if isinstance(first, (list, tuple)):
        return set(second).issubset(first)

    return second in first


def icontains_comparison(first, second):
    return second.lower() in first.lower()


def gt_comparison(first, second):
    return first > second if first is not None else False


def gte_comparison(first, second):
    return first >= second if first is not None else False


def lt_comparison(first, second):
    return first < second if first is not None else False


def lte_comparison(first, second):
    return first <= second if first is not None else False


def in_comparison(first, second):
    if isinstance(first, list):
        return bool(set(first).intersection(set(second)))

    return first in second if first is not None else False


def startswith_comparison(first, second):
    return first.startswith(second)


def istartswith_comparison(first, second):
    return first.lower().startswith(second.lower())


def endswith_comparison(first, second):
    return first.endswith(second)


def iendswith_comparison(first, second):
    return first.lower().endswith(second.lower())


def isnull_comparison(first, second):
    return (first is None) == bool(second)


def regex_comparison(first, second):
    return re.search(second, first) is not None


def iregex_comparison(first, second):
    return re.search(second, first, flags=re.I) is not None


def range_comparison(first, second):
    return second[0] <= first <= second[1]


def overlap_comparison(first, second):
    return bool(set(first).intersection(set(second)))
