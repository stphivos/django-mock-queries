from mock import MagicMock, PropertyMock
from operator import attrgetter

from .constants import *
from .exceptions import *
from .utils import matches, merge, intersect, get_attribute


class MockBase(MagicMock):
    def return_self(self, *args, **kwargs):
        return self

    def __init__(self, *args, **kwargs):
        for x in kwargs.pop('return_self_methods', []):
            kwargs.update({x: self.return_self})

        super(MockBase, self).__init__(*args, **kwargs)


def MockSet(*initial_items, **kwargs):
    items = list(initial_items)
    clone = kwargs.get('clone', None)

    mock_set = MockBase(spec=DjangoQuerySet, return_self_methods=[
        'all',
        'only',
        'defer',
        'using',
        'select_related',
        'prefetch_related',
        'select_for_update'
    ])
    mock_set.cls = clone.cls if clone else kwargs.get('cls', empty_func)
    mock_set.flat = clone.flat if clone else None
    mock_set.projection = clone.projection if clone else None
    mock_set.count = MagicMock(side_effect=lambda: len(items))

    def project(index, source_items=None):
        target_items = source_items or items
        if not mock_set.projection:
            return target_items[index]
        elif mock_set.flat:
            return getattr(target_items[index], mock_set.projection[0])
        else:
            return tuple([getattr(target_items[index], x) for x in mock_set.projection])

    mock_set.project = MagicMock(side_effect=project)

    def add(*model):
        items.extend(model)

    mock_set.add = MagicMock(side_effect=add)

    def remove(**attrs):
        for x in matches(*items, **attrs):
            items.remove(x)

    mock_set.remove = MagicMock(side_effect=remove)

    def filter_q(source, query):
        results = []

        for exp in query.children:
            filtered = list(matches(*source, **{exp[0]: exp[1]}))

            if not results:
                results = filtered
                continue

            if query.connector == CONNECTORS_OR:
                results = merge(results, filtered)
            elif query.connector == CONNECTORS_AND:
                results = intersect(results, filtered)

        return results

    mock_set.filter_q = MagicMock(side_effect=filter_q)

    def filter(*args, **attrs):
        results = list(items)
        for x in args:
            if isinstance(x, DjangoQ):
                results = filter_q(results, x)
            else:
                raise ArgumentNotSupported()
        return MockSet(*matches(*results, **attrs), clone=mock_set)

    mock_set.filter = MagicMock(side_effect=filter)

    def exclude(*args, **attrs):
        excluded = filter(*args, **attrs)
        results = [item for item in items if item not in excluded]
        return MockSet(*results, clone=mock_set)

    mock_set.exclude = MagicMock(side_effect=exclude)

    def clear():
        del items[:]

    mock_set.clear = MagicMock(side_effect=clear)

    def exists():
        return len(items) > 0

    mock_set.exists = MagicMock(side_effect=exists)

    def get_item(x):
        return project(x)

    mock_set.__getitem__ = MagicMock(side_effect=get_item)

    def aggregate(*args, **kwargs):
        result = {}
        for expr in set(args):
            kwargs['{0}__{1}'.format(expr.source_expressions[0].name, expr.function).lower()] = expr
        for alias, expr in kwargs.items():
            values = [y for y in [getattr(x, expr.source_expressions[0].name) for x in items] if y is not None]
            expr_result = None
            if len(values) > 0:
                expr_result = {
                    AGGREGATES_SUM: lambda: sum(values),
                    AGGREGATES_COUNT: lambda: len(values),
                    AGGREGATES_MAX: lambda: max(values),
                    AGGREGATES_MIN: lambda: min(values),
                    AGGREGATES_AVG: lambda: sum(values) / len(values)
                }[expr.function]()
            if len(values) == 0 and expr.function == AGGREGATES_COUNT:
                expr_result = 0
            result[alias] = expr_result
        return result

    mock_set.aggregate = MagicMock(side_effect=aggregate)

    def order_by(*fields):
        results = items
        for field in reversed(fields):
            is_reversed = field.startswith('-')
            attr = field[1:] if is_reversed else field
            results = sorted(results,
                             key=lambda r: get_attribute(r, attr),
                             reverse=is_reversed)
        return MockSet(*results, clone=mock_set)

    mock_set.order_by = MagicMock(side_effect=order_by)

    def distinct():
        results = set(items)
        return MockSet(*results, clone=mock_set)

    mock_set.distinct = MagicMock(side_effect=distinct)

    def latest(field):
        results = sorted(items, key=attrgetter(field), reverse=True)
        if len(results) == 0:
            raise ObjectDoesNotExist()
        return project(0, source_items=results)

    mock_set.latest = MagicMock(side_effect=latest)

    def earliest(field):
        results = sorted(items, key=attrgetter(field))
        if len(results) == 0:
            raise ObjectDoesNotExist()
        return project(0, source_items=results)

    mock_set.earliest = MagicMock(side_effect=earliest)

    def first():
        for item in items:
            return item

    mock_set.first = MagicMock(side_effect=first)

    def last():
        return items and items[-1] or None

    mock_set.last = MagicMock(side_effect=last)

    def __iter__():
        return iter([project(i) for i, v in enumerate(items)])

    mock_set.__iter__ = MagicMock(side_effect=__iter__)

    def create(**attrs):
        obj = mock_set.cls(**attrs)
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
            return project(0, source_items=results)

    mock_set.get = MagicMock(side_effect=get)

    def get_or_create(**attrs):
        results = filter(**attrs)
        if not results.exists():
            return create(**attrs), True
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return project(0, source_items=results), False

    mock_set.get_or_create = MagicMock(side_effect=get_or_create)

    def values_list(*fields, **kwargs):
        flat = kwargs.pop('flat', False)

        if kwargs:
            raise TypeError('Unexpected keyword arguments to values_list: %s' % (list(kwargs),))
        if flat and len(fields) > 1:
            raise TypeError('`flat` is not valid when values_list is called with more than one field.')

        mock_set.flat = flat
        mock_set.projection = fields

        return MockSet(*items, clone=mock_set)

    mock_set.values_list = MagicMock(side_effect=values_list)

    return mock_set


def MockModel(cls=None, mock_name=None, spec_set=None, **attrs):
    mock_attrs = dict(spec=cls, name=mock_name, spec_set=spec_set)
    mock_model = MagicMock(**mock_attrs)

    if mock_name:
        setattr(type(mock_model), '__repr__', MagicMock(return_value=mock_name))

    for key, value in attrs.items():
        setattr(type(mock_model), key, PropertyMock(return_value=value))

    return mock_model


def empty_func(*args, **kwargs):
    pass
