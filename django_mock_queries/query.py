import datetime
from collections import OrderedDict
from mock import Mock, MagicMock, PropertyMock

from .constants import *
from .exceptions import *
from .utils import (
    matches, merge, intersect, get_attribute, validate_mock_set, is_list_like_iter, flatten_list, truncate, hash_dict
)


class MockSet(MagicMock):
    EVENT_ADDED = 'added'
    EVENT_UPDATED = 'updated'
    EVENT_SAVED = 'saved'
    EVENT_DELETED = 'deleted'
    SUPPORTED_EVENTS = [EVENT_ADDED, EVENT_UPDATED, EVENT_SAVED, EVENT_DELETED]
    RETURN_SELF_METHODS = [
        'all',
        'only',
        'defer',
        'using',
        'select_related',
        'prefetch_related',
        'select_for_update'
    ]

    def __init__(self, *initial_items, **kwargs):
        clone = kwargs.pop('clone', None)
        model = kwargs.pop('model', None)

        for x in self.RETURN_SELF_METHODS:
            kwargs.update({x: self._return_self})

        super(MockSet, self).__init__(spec=DjangoQuerySet, **kwargs)

        self.items = list()
        self.clone = clone
        self.model = getattr(clone, 'model', model)
        self.events = {}

        self.add(*initial_items)

        self.__len__ = lambda s: len(s.items)
        self.__iter__ = lambda s: iter(s.items)
        self.__getitem__ = lambda s, k: self.items[k]

    def _return_self(self, *_, **__):
        return self

    def count(self):
        return len(self.items)

    def fire(self, obj, *events):
        for name in events:
            for handler in self.events.get(name, []):
                handler(obj)

    def on(self, event, handler):
        assert event in self.SUPPORTED_EVENTS, event
        self.events[event] = self.events.get(event, []) + [handler]

    def _register_fields(self, obj):
        if not (isinstance(obj, MockModel) or isinstance(obj, Mock)):
            return

        for f in self.model._meta.fields:
            if f.name not in obj.keys():
                setattr(obj, f.name, None)

    def add(self, *models):
        if self.model:
            # Initialize MockModel default fields from MockSet model fields if defined
            for obj in models:
                self._register_fields(obj)

        for model in models:
            self.items.append(model)
            self.fire(model, self.EVENT_ADDED, self.EVENT_SAVED)

    def _filter_single_q(self, source, q_obj, negated):
        if isinstance(q_obj, DjangoQ):
            return self._filter_q(source, q_obj)
        else:
            return matches(negated=negated, *source, **{q_obj[0]: q_obj[1]})

    def _filter_q(self, source, query):
        results = []

        for child in query.children:
            filtered = self._filter_single_q(source, child, query.negated)

            if filtered:
                if not results or query.connector == CONNECTORS_OR:
                    results = merge(results, filtered)
                else:
                    results = intersect(results, filtered)
            elif query.connector == CONNECTORS_AND:
                return []

        return results

    def filter(self, *args, **attrs):
        results = list(self.items)
        for x in args:
            if isinstance(x, DjangoQ):
                results = self._filter_q(results, x)
            else:
                raise ArgumentNotSupported()
        return MockSet(*matches(*results, **attrs), clone=self)

    def exclude(self, *args, **attrs):
        excluded = self.filter(*args, **attrs)
        results = [item for item in self.items if item not in excluded]
        return MockSet(*results, clone=self)

    def exists(self):
        return len(self.items) > 0

    def aggregate(self, *args, **kwargs):
        result = {}

        for expr in set(args):
            kwargs['{0}__{1}'.format(expr.source_expressions[0].name, expr.function).lower()] = expr

        for alias, expr in kwargs.items():
            values = []
            expr_result = None

            for x in self.items:
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

    def order_by(self, *fields):
        results = self.items
        for field in reversed(fields):
            is_reversed = field.startswith('-')
            attr = field[1:] if is_reversed else field
            results = sorted(results,
                             key=lambda r: get_attribute(r, attr),
                             reverse=is_reversed)
        return MockSet(*results, clone=self)

    def distinct(self, *fields):
        results = OrderedDict()
        for item in self.items:
            key = hash_dict(item, *fields)
            if key not in results:
                results[key] = item
        return MockSet(*results.values(), clone=self)

    def _raise_does_not_exist(self):
        does_not_exist = getattr(self.model, 'DoesNotExist', ObjectDoesNotExist)
        raise does_not_exist()

    def _get_order_fields(self, fields, field_name):
        if fields and field_name is not None:
            raise ValueError('Cannot use both positional arguments and the field_name keyword argument.')

        if field_name is not None:
            # The field_name keyword argument is deprecated in favor of passing positional arguments.
            order_fields = (field_name,)
        elif fields:
            order_fields = fields
        else:
            order_fields = self.model._meta.get_latest_by
            if order_fields and not isinstance(order_fields, (tuple, list)):
                order_fields = (order_fields,)

        if order_fields is None:
            raise ValueError(
                "earliest() and latest() require either fields as positional "
                "arguments or 'get_latest_by' in the model's Meta."
            )

        return order_fields

    def _earliest_or_latest(self, *fields, **field_kwargs):
        """
        Mimic Django's behavior
        https://github.com/django/django/blob/746caf3ef821dbf7588797cb2600fa81b9df9d1d/django/db/models/query.py#L560
        """
        field_name = field_kwargs.get('field_name', None)
        reverse = field_kwargs.get('reverse', False)
        order_fields = self._get_order_fields(fields, field_name)

        results = sorted(
            self.items,
            key=lambda obj: tuple(get_attribute(obj, key) for key in order_fields),
            reverse=reverse,
        )

        if len(results) == 0:
            self._raise_does_not_exist()

        return results[0]

    def earliest(self, *fields, **field_kwargs):
        return self._earliest_or_latest(*fields, **field_kwargs)

    def latest(self, *fields, **field_kwargs):
        return self._earliest_or_latest(*fields, reverse=True, **field_kwargs)

    def first(self):
        for item in self.items:
            return item

    def last(self):
        return self.items and self.items[-1] or None

    def create(self, **attrs):
        validate_mock_set(self, **attrs)

        obj = self.model(**attrs)
        self.add(obj)

        return obj

    def update(self, **attrs):
        validate_mock_set(self, for_update=True, **attrs)

        count = 0
        for item in self.items:
            count += 1
            for k, v in attrs.items():
                setattr(item, k, v)
                self.fire(item, self.EVENT_UPDATED, self.EVENT_SAVED)

        return count

    def _delete_recursive(self, *items_to_remove, **attrs):
        for item in matches(*items_to_remove, **attrs):
            self.items.remove(item)
            self.fire(item, self.EVENT_DELETED)

        if self.clone is not None:
            self.clone._delete_recursive(*items_to_remove, **attrs)

    def delete(self, **attrs):
        # Delete normally doesn't take **attrs - they're only needed for remove
        self._delete_recursive(*self.items, **attrs)

    # The following 2 methods were kept for backwards compatibility and
    # should be removed in the future since they are covered by filter & delete
    def clear(self, **attrs):
        return self.delete(**attrs)

    def remove(self, **attrs):
        return self.delete(**attrs)

    def get(self, **attrs):
        results = self.filter(**attrs)
        if not results.exists():
            self._raise_does_not_exist()
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return results[0]

    def get_or_create(self, defaults=None, **attrs):
        if defaults is not None:
            validate_mock_set(self)
        defaults = defaults or {}
        lookup = attrs.copy()
        attrs.update(defaults)
        results = self.filter(**lookup)
        if not results.exists():
            return self.create(**attrs), True
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            return results[0], False

    def update_or_create(self, defaults=None, **attrs):
        if defaults is not None:
            validate_mock_set(self)
        defaults = defaults or {}
        lookup = attrs.copy()
        attrs.update(defaults)
        results = self.filter(**lookup)
        if not results.exists():
            return self.create(**attrs), True
        elif results.count() > 1:
            raise MultipleObjectsReturned()
        else:
            obj = results[0]
            for k, v in attrs.items():
                setattr(obj, k, v)
                self.fire(obj, self.EVENT_UPDATED, self.EVENT_SAVED)
            return obj, False

    def _item_values(self, item, fields):
        field_buckets = {}
        result_count = 1

        if len(fields) == 0:
            field_names = [f.attname for f in item._meta.concrete_fields]
        else:
            field_names = list(fields)

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

        item_values = []
        for i in range(result_count):
            item_values.append({k: v[i] for k, v in field_buckets.items()})

        return item_values

    def values(self, *fields):
        result = []

        for item in self.items:
            item_values = self._item_values(item, fields)
            result.extend(item_values)

        return MockSet(*result, clone=self)

    def _item_values_list(self, values_dict, fields, flat):
        if flat:
            return values_dict[fields[0]]
        else:
            data = []
            for key in sorted(values_dict.keys(), key=lambda k: fields.index(k)):
                data.append(values_dict[key])
            return tuple(data)

    def values_list(self, *fields, **kwargs):
        flat = kwargs.pop('flat', False)

        if kwargs:
            raise TypeError('Unexpected keyword arguments to values_list: %s' % (list(kwargs),))
        if flat and len(fields) > 1:
            raise TypeError('`flat` is not valid when values_list is called with more than one field.')
        if len(fields) == 0:
            raise NotImplementedError('values_list() with no arguments is not implemented')

        result = []
        item_values_dicts = list(self.values(*fields))

        for values_dict in item_values_dicts:
            result.append(self._item_values_list(values_dict, fields, flat))

        return MockSet(*result, clone=self)

    def _date_values(self, field, kind, order, key_func):
        initial_values = list(self.values_list(field, flat=True))

        return MockSet(*sorted(
            {truncate(x, kind) for x in initial_values},
            key=key_func,
            reverse=True if order == 'DESC' else False
        ), clone=self)

    def dates(self, field, kind, order='ASC'):
        assert kind in ("year", "month", "day"), "'kind' must be one of 'year', 'month' or 'day'."
        assert order in ('ASC', 'DESC'), "'order' must be either 'ASC' or 'DESC'."

        return self._date_values(field, kind, order, lambda y: datetime.date.timetuple(y)[:3])

    def datetimes(self, field, kind, order='ASC'):
        # TODO: Handle `tzinfo` parameter
        assert kind in ("year", "month", "day", "hour", "minute", "second"), \
            "'kind' must be one of 'year', 'month', 'day', 'hour', 'minute' or 'second'."
        assert order in ('ASC', 'DESC'), "'order' must be either 'ASC' or 'DESC'."

        return self._date_values(field, kind, order, lambda y: datetime.datetime.timetuple(y)[:6])


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
