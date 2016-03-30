from mock import MagicMock, PropertyMock
from operator import attrgetter

from .constants import *
from .exceptions import *
from .utils import matches, merge, intersect


class MockBase(MagicMock):
    def __init__(self, *args, **kwargs):
        for x in kwargs.pop('return_self_methods', []):
            kwargs.update({x: lambda: self})

        super(MockBase, self).__init__(*args, **kwargs)


def MockSet(*initial_items, **kwargs):
    items = list(initial_items)
    cls = kwargs.get('cls', empty_func)

    mock_set = MockBase(spec=DjangoQuerySet, return_self_methods=[
        'all',
        'only',
        'defer',
        'using',
        'select_related',
        'prefetch_related',
        'select_for_update'
    ])
    mock_set.count = MagicMock(side_effect=lambda: len(items))

    def add(*model):
        items.extend(model)

    mock_set.add = MagicMock(side_effect=add)

    def remove(**attrs):
        for x in matches(*items, **attrs):
            items.remove(x)

    mock_set.remove = MagicMock(side_effect=remove)

    def filter_q(source, query):
        results = list(source)

        filtered = []
        for exp in query.children:
            filtered.append(MockSet(*matches(*items, **{exp[0]: exp[1]}), cls=cls))

        if query.connector == CONNECTORS_OR:
            for filter_results in filtered:
                results = merge(results, list(filter_results))
        elif query.connector == CONNECTORS_AND:
            for filter_results in filtered:
                results = intersect(results, list(filter_results))

        return results

    def filter(*args, **attrs):
        results = list(items)
        for x in args:
            if isinstance(x, DjangoQ):
                results = filter_q(results, x)
            else:
                raise ArgumentNotSupported()
        return MockSet(*matches(*results, **attrs), cls=cls)

    mock_set.filter = MagicMock(side_effect=filter)

    def clear():
        del items[:]

    mock_set.clear = MagicMock(side_effect=clear)

    def exists():
        return len(items) > 0

    mock_set.exists = MagicMock(side_effect=exists)

    def get_item(index):
        return items[index]

    mock_set.__getitem__ = MagicMock(side_effect=get_item)

    def aggregate(expr):
        # TODO: Support multi expressions in aggregate functions
        values = [getattr(x, expr.source_expressions[0].name) for x in items]
        result = {
            AGGREGATES_SUM: lambda: sum(values),
            AGGREGATES_COUNT: lambda: len(values),
            AGGREGATES_MAX: lambda: max(values),
            AGGREGATES_MIN: lambda: min(values),
            AGGREGATES_AVG: lambda: sum(values) / len(values)
        }[expr.function]()

        output_field = '{0}__{1}'.format(expr.source_expressions[0].name, expr.function).lower()

        return {
            output_field: result
        }

    mock_set.aggregate = MagicMock(side_effect=aggregate)

    def latest(field):
        result = sorted(items, key=attrgetter(field), reverse=True)
        if len(result) == 0:
            raise ObjectDoesNotExist()
        return result[0]

    mock_set.latest = MagicMock(side_effect=latest)

    def earliest(field):
        result = sorted(items, key=attrgetter(field))
        if len(result) == 0:
            raise ObjectDoesNotExist()
        return result[0]

    mock_set.earliest = MagicMock(side_effect=earliest)

    def __iter__():
        return iter(items)

    mock_set.__iter__ = MagicMock(side_effect=__iter__)

    def create(**attrs):
        obj = cls(**attrs)
        if not obj:
            raise ModelNotSpecified()
        obj.save(force_insert=True, using=MagicMock())
        add(obj)
        return obj

    mock_set.create = MagicMock(side_effect=create)

    def get(**attrs):
        results = filter(**attrs)
        if not results.exists():
            raise ObjectDoesNotExist()
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return results[0]

    mock_set.get = MagicMock(side_effect=get)

    def get_or_create(**attrs):
        results = filter(**attrs)
        if not results.exists():
            return create(**attrs), True
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return results[0], False

    mock_set.get_or_create = MagicMock(side_effect=get_or_create)

    return mock_set


def MockModel(cls=None, mock_name=None, **attrs):
    mock_attrs = dict(spec=cls, name=mock_name)
    mock_model = MagicMock(**mock_attrs)

    if mock_name:
        mock_model.name = mock_name

    for key, value in attrs.items():
        setattr(type(mock_model), key, PropertyMock(return_value=value))

    return mock_model


def empty_func(*args, **kwargs):
    pass
