from mock import MagicMock, ANY
from unittest import TestCase

from django.core.exceptions import FieldError
from django.db.models import Q

from django_mock_queries.constants import *
from django_mock_queries.exceptions import ModelNotSpecified, ArgumentNotSupported
from django_mock_queries.query import MockSet, MockModel, MockSetModel
from tests.mock_models import Car, Sedan, Manufacturer


class TestQuery(TestCase):
    def setUp(self):
        self.mock_set = MockSet()

    def test_query_counts_items_in_set(self):
        items = [1, 2, 3]
        assert MockSet(*items).count() == len(items)

    def test_query_adds_items_to_set(self):
        items = [1, 2, 3]
        self.mock_set.add(*items)
        assert list(self.mock_set) == items

    def test_query_removes_items_from_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)

        self.mock_set.add(item_1, item_2)
        self.mock_set.remove(foo=1)
        items = list(self.mock_set)

        assert item_1 not in items
        assert item_2 in items

    def test_query_filters_items_by_attributes(self):
        item_1 = MockModel(foo=1, bar='a')
        item_2 = MockModel(foo=1, bar='b')
        item_3 = MockModel(foo=2, bar='b')

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(foo=1, bar='b'))

        assert item_1 not in results
        assert item_2 in results
        assert item_3 not in results

    def test_query_filters_items_by_q_object_or(self):
        item_1 = MockModel(mock_name='#1', foo=1)
        item_2 = MockModel(mock_name='#2', foo=2)
        item_3 = MockModel(mock_name='#3', foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(Q(foo=1) | Q(foo=2)))

        assert item_1 in results
        assert item_2 in results
        assert item_3 not in results

    def test_query_filters_items_by_q_object_and(self):
        item_1 = MockModel(mock_name='#1', foo=1, bar='a')
        item_2 = MockModel(mock_name='#2', foo=1, bar='b')
        item_3 = MockModel(mock_name='#3', foo=3, bar='b')

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(Q(foo=1) & Q(bar='b')))

        assert item_1 not in results
        assert item_2 in results
        assert item_3 not in results

    def test_query_filters_items_by_unsupported_object(self):
        bogus_filter = 'This is not a filter.'

        with self.assertRaises(ArgumentNotSupported):
            self.mock_set.filter(bogus_filter)

    def test_query_filters_model_objects(self):
        item_1 = Car(speed=1)
        item_2 = Sedan(speed=2)
        item_3 = Car(speed=3)

        item_2.sedan = item_2

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(speed=3))

        assert results == [item_3]

    def test_query_filters_related_model_objects(self):
        item_1 = Car(make=Manufacturer(name='apple'))
        item_2 = Car(make=Manufacturer(name='banana'))
        item_3 = Car(make=Manufacturer(name='cherry'))

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(make__name='cherry'))

        assert results == [item_3]

    def test_query_filters_model_objects_by_subclass(self):
        item_1 = Car(speed=1)
        item_2 = Sedan(speed=2)
        item_3 = Car(speed=3)

        item_2.sedan = item_2

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(sedan__isnull=False))

        assert results == [item_2]

    def test_query_filters_model_objects_by_pk(self):
        item_1 = Car(speed=1, id=101)
        item_2 = Car(speed=2, id=102)

        self.mock_set.add(item_1, item_2)
        results = list(self.mock_set.filter(pk=102))

        assert results == [item_2]

    def test_convert_to_pks(self):
        car1 = Car(id=101)
        car2 = Car(id=102)
        car3 = Car(id=103)

        old_cars = MockSet(car1, car2)
        all_cars = MockSet(car1, car2, car3)

        matches = all_cars.filter(pk__in=old_cars)

        self.assertEqual(list(old_cars), list(matches))

    def test_query_filters_model_objects_by_bad_field(self):
        item_1 = Car(speed=1)
        item_2 = Sedan(speed=2)
        item_3 = Car(speed=3)

        item_2.sedan = item_2

        self.mock_set.add(item_1, item_2, item_3)
        with self.assertRaisesRegexp(
                FieldError,
                r"Cannot resolve keyword 'bad_field' into field\. "
                r"Choices are 'id', 'make', 'make_id', 'model', 'passengers', 'sedan', 'speed'\."):
            self.mock_set.filter(bad_field='bogus')

    def test_query_exclude(self):
        item_1 = MockModel(foo=1, bar='a')
        item_2 = MockModel(foo=1, bar='b')
        item_3 = MockModel(foo=2, bar='b')

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.exclude(foo=1, bar='b'))

        assert item_1 in results, results
        assert item_2 not in results, results
        assert item_3 in results, results

    def test_query_clears_all_items_from_set(self):
        self.mock_set.add(1, 2, 3)
        self.mock_set.clear()
        assert list(self.mock_set) == []

    def test_query_exists_returns_true_when_items_above_zero_otherwise_false(self):
        assert self.mock_set.exists() is False
        self.mock_set.add(1)
        assert self.mock_set.exists() is True

    def test_query_indexing_set_returns_nth_item(self):
        items = [1, 2, 3]
        self.mock_set.add(*items)
        assert self.mock_set[1] == items[1]

    def test_query_aggregate_performs_sum_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_SUM, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__sum'] == sum([x.foo for x in items if x.foo is not None])

    def test_query_aggregate_performs_count_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_COUNT, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__count'] == len([x.foo for x in items if x.foo is not None])

    def test_query_aggregate_performs_max_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_MAX, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__max'] == max([x.foo for x in items if x.foo is not None])

    def test_query_aggregate_performs_min_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_MIN, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__min'] == min([x.foo for x in items if x.foo is not None])

    def test_query_aggregate_performs_avg_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_AVG, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__avg'] == sum(
            [x.foo for x in items if x.foo is not None]
        ) / len(
            [x.foo for x in items if x.foo is not None]
        )

    def test_query_aggregate_with_none_only_field_values_performs_correct_aggregation(self):
        items = [
            MockModel(foo=None),
            MockModel(foo=None),
            MockModel(foo=None),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr_sum = MagicMock(function=AGGREGATES_SUM, source_expressions=[MockModel(name='foo')])
        expr_max = MagicMock(function=AGGREGATES_MAX, source_expressions=[MockModel(name='foo')])
        expr_min = MagicMock(function=AGGREGATES_MIN, source_expressions=[MockModel(name='foo')])
        expr_count = MagicMock(function=AGGREGATES_COUNT, source_expressions=[MockModel(name='foo')])
        expr_avg = MagicMock(function=AGGREGATES_AVG, source_expressions=[MockModel(name='foo')])

        result_sum = self.mock_set.aggregate(expr_sum)
        result_max = self.mock_set.aggregate(expr_max)
        result_min = self.mock_set.aggregate(expr_min)
        result_count = self.mock_set.aggregate(expr_count)
        result_avg = self.mock_set.aggregate(expr_avg)

        assert result_sum['foo__sum'] is None
        assert result_max['foo__max'] is None
        assert result_min['foo__min'] is None
        assert result_count['foo__count'] == 0
        assert result_avg['foo__avg'] is None

    def test_query_aggregate_multiple_params_aggregation(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr_sum = MagicMock(function=AGGREGATES_SUM, source_expressions=[MockModel(name='foo')])
        expr_max = MagicMock(function=AGGREGATES_MAX, source_expressions=[MockModel(name='foo')])
        expr_min = MagicMock(function=AGGREGATES_MIN, source_expressions=[MockModel(name='foo')])
        expr_count = MagicMock(function=AGGREGATES_COUNT, source_expressions=[MockModel(name='foo')])
        expr_avg = MagicMock(function=AGGREGATES_AVG, source_expressions=[MockModel(name='foo')])

        result = self.mock_set.aggregate(expr_sum, expr_max, expr_min, expr_count, expr_avg,
                                         sum=expr_sum, max=expr_max, min=expr_min, count=expr_count, avg=expr_avg)

        assert result['foo__sum'] == sum([x.foo for x in items if x.foo is not None])
        assert result['foo__max'] == max([x.foo for x in items if x.foo is not None])
        assert result['foo__min'] == min([x.foo for x in items if x.foo is not None])
        assert result['foo__count'] == len([x.foo for x in items if x.foo is not None])
        assert result['foo__avg'] == sum(
            [x.foo for x in items if x.foo is not None]
        ) / len(
            [x.foo for x in items if x.foo is not None]
        )
        assert result['sum'] == sum([x.foo for x in items if x.foo is not None])
        assert result['max'] == max([x.foo for x in items if x.foo is not None])
        assert result['min'] == min([x.foo for x in items if x.foo is not None])
        assert result['count'] == len([x.foo for x in items if x.foo is not None])
        assert result['avg'] == sum(
            [x.foo for x in items if x.foo is not None]
        ) / len(
            [x.foo for x in items if x.foo is not None]
        )

    def test_query_aggregate_multiple_params_with_none_only_field_values_aggregation_with_none(self):
        items = [
            MockModel(foo=None),
            MockModel(foo=None),
            MockModel(foo=None),
            MockModel(foo=None)
        ]
        self.mock_set.add(*items)

        expr_sum = MagicMock(function=AGGREGATES_SUM, source_expressions=[MockModel(name='foo')])
        expr_max = MagicMock(function=AGGREGATES_MAX, source_expressions=[MockModel(name='foo')])
        expr_min = MagicMock(function=AGGREGATES_MIN, source_expressions=[MockModel(name='foo')])
        expr_count = MagicMock(function=AGGREGATES_COUNT, source_expressions=[MockModel(name='foo')])
        expr_avg = MagicMock(function=AGGREGATES_AVG, source_expressions=[MockModel(name='foo')])

        result = self.mock_set.aggregate(expr_sum, expr_max, expr_min, expr_count, expr_avg,
                                         sum=expr_sum, max=expr_max, min=expr_min, count=expr_count, avg=expr_avg)

        assert result['foo__sum'] is None
        assert result['foo__max'] is None
        assert result['foo__min'] is None
        assert result['foo__count'] == 0
        assert result['foo__avg'] is None
        assert result['sum'] is None
        assert result['max'] is None
        assert result['min'] is None
        assert result['count'] == 0
        assert result['avg'] is None

    def test_query_aggregate_with_no_params_returns_empty_dict(self):
        assert self.mock_set.aggregate() == {}

    def test_query_aggregate_multiple_params_expression_distinction(self):
        expr_sum = MagicMock(function=AGGREGATES_SUM, source_expressions=[MockModel(name='foo')])
        expr_max = MagicMock(function=AGGREGATES_MAX, source_expressions=[MockModel(name='foo')])
        expr_min = MagicMock(function=AGGREGATES_MIN, source_expressions=[MockModel(name='foo')])
        expr_count = MagicMock(function=AGGREGATES_COUNT, source_expressions=[MockModel(name='foo')])
        expr_avg = MagicMock(function=AGGREGATES_AVG, source_expressions=[MockModel(name='foo')])

        result = self.mock_set.aggregate(expr_sum, expr_max, expr_min, expr_count, expr_avg,
                                         expr_sum, expr_max, expr_min, expr_count, expr_avg,
                                         a=expr_max, b=expr_max, c=expr_min, d=expr_min,
                                         e=expr_sum, f=expr_sum, g=expr_avg, h=expr_avg,
                                         i=expr_count, j=expr_count)

        assert len(result) == 15

    def test_query_latest_returns_the_last_element_from_ordered_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.latest('foo')

        assert latest == item_3

    def test_query_first_none(self):
        first = self.mock_set.first()

        assert first is None, first

    def test_query_first(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        first = self.mock_set.first()

        assert first == item_3, first

    def test_query_last_none(self):
        last = self.mock_set.last()

        assert last is None, last

    def test_query_last(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        last = self.mock_set.last()

        assert last == item_2, last

    def test_query_latest_raises_error_exist_when_empty_set(self):
        self.mock_set.clear()
        self.assertRaises(ObjectDoesNotExist, self.mock_set.latest, 'foo')

    def test_query_earliest_returns_the_first_element_from_ordered_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.earliest('foo')

        assert latest == item_1

    def test_query_earliest_raises_error_exist_when_empty_set(self):
        self.mock_set.clear()
        self.assertRaises(ObjectDoesNotExist, self.mock_set.earliest, 'foo')

    def test_query_order_by(self):
        item_1 = MockModel(foo=1, bar='a', mock_name='item_1')
        item_2 = MockModel(foo=1, bar='c', mock_name='item_2')
        item_3 = MockModel(foo=2, bar='b', mock_name='item_3')

        self.mock_set.add(item_1, item_3, item_2)
        results = list(self.mock_set.order_by('foo', 'bar'))

        assert results == [item_1, item_2, item_3], results

    def test_query_order_by_descending(self):
        item_1 = MockModel(foo=1, bar='c', mock_name='item_1')
        item_2 = MockModel(foo=1, bar='a', mock_name='item_2')
        item_3 = MockModel(foo=2, bar='b', mock_name='item_3')

        self.mock_set.add(item_2, item_3, item_1)
        results = list(self.mock_set.order_by('foo', '-bar'))

        assert results == [item_1, item_2, item_3], results

    def test_query_distinct(self):
        item_1 = MockModel(foo=1, mock_name='item_1')
        item_2 = MockModel(foo=2, mock_name='item_2')
        item_3 = MockModel(foo=3, mock_name='item_3')

        self.mock_set.add(item_2, item_3, item_1, item_3)
        results = list(self.mock_set.distinct().order_by('foo'))

        assert results == [item_1, item_2, item_3], results

    def test_query_implements_iterator_on_items(self):
        items = [1, 2, 3]
        assert [x for x in MockSet(*items)] == items

    def test_query_creates_new_model_and_adds_to_set(self):
        qs = MockSet(cls=MockModel)

        attrs = dict(foo=1, bar='a')
        obj = qs.create(**attrs)

        obj.save.assert_called_once_with(force_insert=True, using=ANY)
        assert obj in [x for x in qs]

        for k, v in attrs.items():
            assert getattr(obj, k, None) == v

    def test_query_create_raises_model_not_specified_when_mock_set_called_without_cls(self):
        qs = MockSet()
        attrs = dict(foo=1, bar='a')
        self.assertRaises(ModelNotSpecified, qs.create, **attrs)

    def test_query_creates_new_model_based_on_mocksetmodel(self):
        qs = MockSet(
            model=MockSetModel('first', 'second', 'third'),
            cls=MockModel
        )
        attrs = dict(first=1, third=3)
        obj = qs.create(**attrs)
        obj.save.assert_called_once_with(force_insert=True, using=ANY)
        assert obj in [x for x in qs]
        for k, v in attrs.items():
            assert getattr(obj, k, None) == v
        assert getattr(obj, 'second', None) is None

    def test_query_create_raises_value_error_when_kwarg_key_is_not_in_concrete_fields(self):
        qs = MockSet(
            model=MockSetModel('first', 'second', 'third'),
            cls=MockModel
        )
        attrs = dict(first=1, second=2, third=3, fourth=4)
        with self.assertRaises(ValueError):
            qs.create(**attrs)

    def test_query_gets_unique_match_by_attrs_from_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        result = self.mock_set.get(foo=2)

        assert item_2 == result

    def test_query_get_raises_does_not_exist_when_no_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        self.assertRaises(ObjectDoesNotExist, self.mock_set.get, foo=4)

    def test_query_get_raises_specific_exception(self):
        item_1 = Car(model='battle')
        item_2 = Car(model='pious')
        item_3 = Car(model='hummus')

        self.mock_set = MockSet(item_1, item_2, item_3, cls=Car)
        self.assertRaises(Car.DoesNotExist, self.mock_set.get, model='clowncar')

    def test_filter_keeps_class(self):
        item_1 = Car(model='battle')
        item_2 = Car(model='pious')
        item_3 = Car(model='hummus')

        self.mock_set = MockSet(item_1, item_2, item_3, cls=Car)
        filtered = self.mock_set.filter(model__endswith='s')
        self.assertRaises(Car.DoesNotExist, filtered.get, model='clowncar')

    def test_query_get_raises_does_multiple_objects_returned_when_more_than_one_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=1)
        item_3 = MockModel(foo=2)

        self.mock_set.add(item_1, item_2, item_3)
        self.assertRaises(MultipleObjectsReturned, self.mock_set.get, foo=1)

    def test_query_get_or_create_gets_existing_unique_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        obj, created = self.mock_set.get_or_create(foo=2)

        assert obj == item_2
        assert created is False

    def test_query_get_or_create_raises_does_multiple_objects_returned_when_more_than_one_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=1)
        item_3 = MockModel(foo=2)

        self.mock_set.add(item_1, item_2, item_3)
        self.assertRaises(MultipleObjectsReturned, self.mock_set.get_or_create, foo=1)

    def test_query_get_or_create_creates_new_model_when_no_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        qs = MockSet(cls=MockModel)
        qs.add(item_1, item_2, item_3)
        obj, created = qs.get_or_create(foo=4)

        assert hasattr(obj, 'foo') and obj.foo == 4
        assert created is True

    def test_query_get_or_create_gets_existing_unique_match_with_defaults(self):
        qs = MockSet(
            cls=MockModel,
            model=MockSetModel('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        obj, created = qs.get_or_create(defaults={'first': 3, 'third': 1}, second=2)

        assert hasattr(obj, 'second') and obj.second == 2
        assert created is False

    def test_query_get_or_create_raises_does_multiple_objects_returned_when_more_than_one_match_with_defaults(self):
        qs = MockSet(
            cls=MockModel,
            model=MockSetModel('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(first=1)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        qs.add(item_1, item_2, item_3)
        with self.assertRaises(MultipleObjectsReturned):
            qs.get_or_create(first=1, defaults={'second': 2})

    def test_query_get_or_create_creates_new_model_when_no_match_with_defaults(self):
        qs = MockSet(
            cls=MockModel,
            model=MockSetModel('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        obj, created = qs.get_or_create(defaults={'first': 3, 'third': 2}, second=1)

        assert hasattr(obj, 'first') and obj.first == 3
        assert hasattr(obj, 'second') and obj.second == 1
        assert hasattr(obj, 'third') and obj.third == 2
        assert created is True

    def test_query_get_or_create_raises_value_error_when_defaults_passed_without_mockset_model(self):
        qs = MockSet(
            cls=MockModel
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        with self.assertRaises(ValueError):
            qs.get_or_create(defaults={'first': 3, 'third': 2}, second=1)

    def test_query_return_self_methods_accept_any_parameters_and_return_instance(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        assert qs == qs.all()
        assert qs == qs.only('f1')
        assert qs == qs.defer('f2', 'f3')
        assert qs == qs.using('default')
        assert qs == qs.select_related('t1', 't2')
        assert qs == qs.prefetch_related('t3', 't4')
        assert qs == qs.select_for_update()

    def test_query_values_list_raises_type_error_when_kwargs_other_than_flat_specified(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(TypeError, qs.values_list, arg='value')

    def test_query_values_list_raises_type_error_when_flat_specified_with_multiple_fields(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(TypeError, qs.values_list, 'foo', 'bar', flat=True)

    def test_query_values_list_raises_attribute_error_when_field_is_not_in_meta_concrete_fields(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(AttributeError, qs.values_list, 'bar')

    def test_query_values_list_raises_not_implemented_if_no_fields_specified(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(NotImplementedError, qs.values_list)

    def test_query_values_list(self):
        item_1 = MockModel(foo=1, bar=3)
        item_2 = MockModel(foo=2, bar=4)

        qs = MockSet(item_1, item_2)
        results_flat = qs.values_list('foo', flat=True)
        results_single_fields = qs.values_list('foo')
        results_with_fields = qs.values_list('foo', 'bar')

        assert results_flat[0] == 1
        assert results_flat[1] == 2
        assert results_single_fields[0] == (1,)
        assert results_single_fields[1] == (2,)
        assert results_with_fields[0] == (1, 3)
        assert results_with_fields[1] == (2, 4)

    def test_query_values_raises_attribute_error_when_field_is_not_in_meta_concrete_fields(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(AttributeError, qs.values, 'bar')

    def test_query_values(self):
        item_1 = MockModel(foo=1, bar=3, foobar=5)
        item_2 = MockModel(foo=2, bar=4, foobar=6)

        qs = MockSet(item_1, item_2)

        results_all = qs.values()
        results_with_fields = qs.values('foo', 'bar')

        assert results_all[0]['foo'] == 1
        assert results_all[0]['bar'] == 3
        assert results_all[0]['foobar'] == 5
        assert results_all[1]['foo'] == 2
        assert results_all[1]['bar'] == 4
        assert results_all[1]['foobar'] == 6

        assert results_with_fields[0]['foo'] == 1
        assert results_with_fields[0]['bar'] == 3
        assert results_with_fields[1]['foo'] == 2
        assert results_with_fields[1]['bar'] == 4

    def test_length1(self):
        q = MockSet(MockModel())

        n = len(q)

        self.assertEqual(1, n)

    def test_length2(self):
        q = MockSet(MockModel(), MockModel())

        n = len(q)

        self.assertEqual(2, n)

    def test_mocksetmodel_raises_value_error_when_args_length_is_zero(self):
        with self.assertRaises(ValueError):
            MockSetModel()
