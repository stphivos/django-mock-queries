from mock import Mock, MagicMock, PropertyMock
from operator import attrgetter

from .constants import *
from .exceptions import *
from .utils import matches, merge, intersect, get_attribute, validate_mock_set, is_list_like_iter, flatten_list


class MockBase(MagicMock):
    def return_self(self, *args, **kwargs):
        return self

    def __init__(self, *args, **kwargs):
        for x in kwargs.pop('return_self_methods', []):
            kwargs.update({x: self.return_self})

        super(MockBase, self).__init__(*args, **kwargs)


def MockSet(*initial_items, **kwargs):
    items = list()
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
    mock_set.count = MagicMock(side_effect=lambda: len(items))
    mock_set.model = clone.model if clone else kwargs.get('model', None)
    mock_set.__len__ = MagicMock(side_effect=lambda: len(items))

    def add(*models):
        # Initialize MockModel default fields from MockSet model fields if defined
        if mock_set.model:
            for model in models:
                if isinstance(model, MockModel) or isinstance(model, Mock):
                    [setattr(model, f.name, None) for f in mock_set.model._meta.fields if f.name not in model.keys()]

        items.extend(models)

    add(*initial_items)
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
        return items[x]

    mock_set.__getitem__ = MagicMock(side_effect=get_item)

    def aggregate(*args, **kwargs):
        result = {}

        for expr in set(args):
            kwargs['{0}__{1}'.format(expr.source_expressions[0].name, expr.function).lower()] = expr

        for alias, expr in kwargs.items():
            values = []
            expr_result = None

            for x in items:
                val = get_attribute(x, expr.source_expressions[0].name, related_set_singular=True)[0]
                if val is None:
                    continue
                values.extend(val if is_list_like_iter(val) else [val])

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

    def raise_does_not_exist():
        does_not_exist = getattr(mock_set.model, 'DoesNotExist', ObjectDoesNotExist)
        raise does_not_exist()

    def latest(field):
        results = sorted(items, key=attrgetter(field), reverse=True)
        if len(results) == 0:
            raise_does_not_exist()
        return results[0]

    mock_set.latest = MagicMock(side_effect=latest)

    def earliest(field):
        results = sorted(items, key=attrgetter(field))
        if len(results) == 0:
            raise_does_not_exist()
        return results[0]

    mock_set.earliest = MagicMock(side_effect=earliest)

    def first():
        for item in items:
            return item

    mock_set.first = MagicMock(side_effect=first)

    def last():
        return items and items[-1] or None

    mock_set.last = MagicMock(side_effect=last)

    def __iter__():
        return iter([items[i] for i, v in enumerate(items)])

    mock_set.__iter__ = MagicMock(side_effect=__iter__)

    def create(**attrs):
        validate_mock_set(mock_set)
        for k in attrs.keys():
            if k not in [f.attname for f in mock_set.model._meta.concrete_fields]:
                raise ValueError('{} is an invalid keyword argument for this function'.format(k))
        for field in mock_set.model._meta.concrete_fields:
            if field.attname not in attrs.keys():
                attrs[field.attname] = None
        obj = mock_set.model(**attrs)
        obj.save(force_insert=True, using=MagicMock())
        add(obj)
        return obj

    mock_set.create = MagicMock(side_effect=create)

    def get(**attrs):
        results = filter(**attrs)
        if not results.exists():
            raise_does_not_exist()
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return results[0]

    mock_set.get = MagicMock(side_effect=get)

    def get_or_create(defaults=None, **attrs):
        if defaults is not None:
            validate_mock_set(mock_set)
        defaults = defaults or {}
        lookup = attrs.copy()
        attrs.update(defaults)
        results = filter(**lookup)
        if not results.exists():
            return create(**attrs), True
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return results[0], False

    mock_set.get_or_create = MagicMock(side_effect=get_or_create)

    def values(*fields):
        result = []
        for item in items:
            if len(fields) == 0:
                field_names = [f.attname for f in item._meta.concrete_fields]
            else:
                field_names = list(fields)

            field_buckets = {}
            result_count = 1

            for field in sorted(field_names, key=lambda k: k.count('__')):
                value = get_attribute(item, field, related_set_singular=True)[0]

                if is_list_like_iter(value):
                    value = flatten_list(value)
                    result_count = max(result_count, len(value))

                    for bucket, data in field_buckets.items():
                        while len(data) < result_count:
                            data.append(data[-1])

                    field_buckets[field] = value
                else:
                    field_buckets[field] = [value]

            item_dicts = []
            for i in range(result_count):
                item_dicts.append({k: v[i] for k, v in field_buckets.items()})

            result.extend(item_dicts)

        return MockSet(*result, clone=mock_set)

    mock_set.values = MagicMock(side_effect=values)

    def values_list(*fields, **kwargs):
        flat = kwargs.pop('flat', False)

        if kwargs:
            raise TypeError('Unexpected keyword arguments to values_list: %s' % (list(kwargs),))
        if flat and len(fields) > 1:
            raise TypeError('`flat` is not valid when values_list is called with more than one field.')
        if len(fields) == 0:
            raise NotImplementedError('values_list() with no arguments is not implemented')

        result = []
        for item in list(values(*fields)):
            if flat:
                result.append(item[fields[0]])
            else:
                data = []
                for key in sorted(item.keys(), key=lambda k: fields.index(k)):
                    data.append(item[key])
                result.append(tuple(data))

        return MockSet(*result, clone=mock_set)

    mock_set.values_list = MagicMock(side_effect=values_list)

    return mock_set


class MockModel(dict):
    def __init__(self, *args, **kwargs):
        self.save = PropertyMock()
        super(MockModel, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        return self.get(item, None)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __hash__(self):
        return hash(tuple(sorted(self.items())))

    def __call__(self, *args, **kwargs):
        return MockModel(*args, **kwargs)

    @property
    def _meta(self):
        keys_list = list(self.keys())
        keys_list.remove('save')
        return MockOptions(*keys_list)


def create_model(*fields):
    if len(fields) == 0:
        raise ValueError('create_model() is called without fields specified')
    return MockModel(**{f: None for f in fields})


class MockOptions(object):
    def __init__(self, *field_names):
        fields = {name: MockField(name) for name in field_names}

        for key in ('_forward_fields_map', 'parents', 'fields_map'):
            self.__dict__[key] = {}

            if key == '_forward_fields_map':
                for name, obj in fields.items():
                    self.__dict__[key][name] = obj

        for key in ('local_concrete_fields', 'concrete_fields', 'fields'):
            self.__dict__[key] = []

            for name, obj in fields.items():
                self.__dict__[key].append(obj)


class MockField(object):
    def __init__(self, field):
        for key in ('name', 'attname'):
            self.__dict__[key] = field
