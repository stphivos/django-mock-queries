import datetime
from collections import OrderedDict
from mock import Mock, MagicMock, PropertyMock

from .constants import *
from .exceptions import *
from .utils import (
    matches, merge, intersect, get_attribute, validate_mock_set, is_list_like_iter, flatten_list, truncate, hash_dict
)


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

    mock_set.events = {}

    EVENT_ADDED = 'added'
    EVENT_UPDATED = 'updated'
    EVENT_SAVED = 'saved'
    EVENT_DELETED = 'deleted'
    SUPPORTED_EVENTS = [EVENT_ADDED, EVENT_UPDATED, EVENT_SAVED, EVENT_DELETED]

    def fire(obj, *events):
        for name in events:
            for handler in mock_set.events.get(name, []):
                handler(obj)

    def on(event, handler):
        assert event in SUPPORTED_EVENTS, event
        mock_set.events[event] = mock_set.events.get(event, []) + [handler]

    mock_set.on = MagicMock(side_effect=on)

    def add(*models):
        # Initialize MockModel default fields from MockSet model fields if defined
        if mock_set.model:
            for model in models:
                if isinstance(model, MockModel) or isinstance(model, Mock):
                    [setattr(model, f.name, None) for f in mock_set.model._meta.fields if f.name not in model.keys()]

        for model in models:
            items.append(model)
            fire(model, EVENT_ADDED, EVENT_SAVED)

    add(*initial_items)
    mock_set.add = MagicMock(side_effect=add)

    def filter_q(source, query):
        results = []

        for child in query.children:
            if isinstance(child, DjangoQ):
                filtered = filter_q(source, child)
            else:
                filtered = list(matches(negated=query.negated, *source, **{child[0]: child[1]}))

            if filtered:
                if not results or query.connector == CONNECTORS_OR:
                    results = merge(results, filtered)
                else:
                    results = intersect(results, filtered)
            elif query.connector == CONNECTORS_AND:
                return filtered

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
                val = get_attribute(x, expr.source_expressions[0].name)[0]
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

    def distinct(*fields):
        results = OrderedDict()
        for item in items:
            key = hash_dict(item, *fields)
            if key not in results:
                results[key] = item
        return MockSet(*results.values(), clone=mock_set)

    mock_set.distinct = MagicMock(side_effect=distinct)

    def raise_does_not_exist():
        does_not_exist = getattr(mock_set.model, 'DoesNotExist', ObjectDoesNotExist)
        raise does_not_exist()

    def _earliest_or_latest(*fields, **field_kwargs):
        """
        Mimic Django's behavior
        https://github.com/django/django/blob/746caf3ef821dbf7588797cb2600fa81b9df9d1d/django/db/models/query.py#L560
        """
        field_name = field_kwargs.get('field_name', None)
        reverse = field_kwargs.get('reverse', False)

        if fields and field_name is not None:
            raise ValueError('Cannot use both positional arguments and the field_name keyword argument.')

        if field_name is not None:
            # The field_name keyword argument is deprecated in favor of passing positional arguments.
            order_fields = (field_name,)
        elif fields:
            order_fields = fields
        else:
            order_fields = mock_set.model._meta.get_latest_by
            if order_fields and not isinstance(order_fields, (tuple, list)):
                order_fields = (order_fields,)

        if order_fields is None:
            raise ValueError(
                "earliest() and latest() require either fields as positional "
                "arguments or 'get_latest_by' in the model's Meta."
            )

        results = sorted(items, key=lambda obj: tuple(get_attribute(obj, key) for key in order_fields), reverse=reverse)
        if len(results) == 0:
            raise_does_not_exist()

        return results[0]

    def earliest(*fields, **field_kwargs):
        return _earliest_or_latest(*fields, **field_kwargs)

    mock_set.earliest = MagicMock(side_effect=earliest)

    def latest(*fields, **field_kwargs):
        return _earliest_or_latest(*fields, reverse=True, **field_kwargs)

    mock_set.latest = MagicMock(side_effect=latest)

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
        validate_mock_set(mock_set, **attrs)

        # TODO: Determine the default value for each field and set it to that so django doesn't complain
        # for field in target_fields:
        #     if field not in attrs.keys():
        #         attrs[field] = None

        obj = mock_set.model(**attrs)
        add(obj)

        return obj

    mock_set.create = MagicMock(side_effect=create)

    def update(**attrs):
        validate_mock_set(mock_set, for_update=True, **attrs)

        count = 0
        for item in items:
            count += 1
            for k, v in attrs.items():
                setattr(item, k, v)
                fire(item, EVENT_UPDATED, EVENT_SAVED)

        return count

    mock_set.update = MagicMock(side_effect=update)

    def _delete_recursive(*items_to_remove, **attrs):
        for item in matches(*items_to_remove, **attrs):
            items.remove(item)
            fire(item, EVENT_DELETED)

        if clone:
            clone._delete_recursive(*items_to_remove, **attrs)

    mock_set._delete_recursive = MagicMock(side_effect=_delete_recursive)

    def delete(**attrs):
        # Delete normally doesn't take **attrs - they're only needed for remove
        _delete_recursive(*items, **attrs)

    mock_set.delete = MagicMock(side_effect=delete)

    # The following 2 methods were kept for backwards compatibility and
    # should be removed in the future since they are covered by filter & delete
    mock_set.clear = MagicMock(side_effect=delete)
    mock_set.remove = MagicMock(side_effect=delete)

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
                value = get_attribute(item, field)[0]

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

    def dates(field, kind, order='ASC'):
        assert kind in ("year", "month", "day"), "'kind' must be one of 'year', 'month' or 'day'."
        assert order in ('ASC', 'DESC'), "'order' must be either 'ASC' or 'DESC'."

        initial_values = list(values_list(field, flat=True))

        return MockSet(*sorted(
            {truncate(x, kind) for x in initial_values},
            key=lambda y: datetime.date.timetuple(y)[:3],
            reverse=True if order == 'DESC' else False
        ), clone=mock_set)

    mock_set.dates = MagicMock(side_effect=dates)

    def datetimes(field, kind, order='ASC'):
        # TODO: Handle `tzinfo` parameter
        assert kind in ("year", "month", "day", "hour", "minute", "second"), \
            "'kind' must be one of 'year', 'month', 'day', 'hour', 'minute' or 'second'."
        assert order in ('ASC', 'DESC'), "'order' must be either 'ASC' or 'DESC'."

        initial_values = list(values_list(field, flat=True))

        return MockSet(*sorted(
            {truncate(x, kind) for x in initial_values},
            key=lambda y: datetime.datetime.timetuple(y)[:6],
            reverse=True if order == 'DESC' else False
        ), clone=mock_set)

    mock_set.datetimes = MagicMock(side_effect=datetimes)

    return mock_set


class MockModel(dict):
    def __init__(self, *args, **kwargs):
        super(MockModel, self).__init__(*args, **kwargs)

        self.save = PropertyMock()
        self.__meta = MockOptions(*self.get_fields())

    def __getattr__(self, item):
        return self.get(item, None)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __hash__(self):
        return hash_dict(self)

    def __call__(self, *args, **kwargs):
        return MockModel(*args, **kwargs)

    def get_fields(self):
        skip_keys = ['save', '_MockModel__meta']
        return [key for key in self.keys() if key not in skip_keys]

    @property
    def _meta(self):
        self.__meta.load_fields(*self.get_fields())
        return self.__meta

    def __repr__(self):
        return self.get('mock_name', None) or super(MockModel, self).__repr__()


def create_model(*fields):
    if len(fields) == 0:
        raise ValueError('create_model() is called without fields specified')
    return MockModel(**{f: None for f in fields})


class MockOptions(object):
    def __init__(self, *field_names):
        self.load_fields(*field_names)
        self.get_latest_by = None

    def load_fields(self, *field_names):
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
