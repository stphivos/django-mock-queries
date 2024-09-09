import datetime
import warnings
from unittest import TestCase
from unittest.mock import MagicMock

from django.core.exceptions import FieldError
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q, Avg
from django.db.models.functions import Coalesce

from django_mock_queries.constants import *
from django_mock_queries.exceptions import ModelNotSpecified, ArgumentNotSupported
from django_mock_queries.query import MockSet, MockModel, create_model
from django_mock_queries.mocks import mocked_relations
from tests.mock_models import Car, CarVariation, Sedan, Manufacturer


class TestQuery(TestCase):
    def setUp(self):
        self.mock_set = MockSet()

    def tearDown(self):
        self.mock_set.clear()

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

    def test_query_filters_items_by_boolean_attributes(self):
        item_1 = MockModel(foo=True, bar=True)
        item_2 = MockModel(foo=True, bar=False)
        item_3 = MockModel(foo=False, bar=False)

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(foo=True, bar=False))

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

    def test_query_filters_items_by_q_object_with_negation(self):
        item_1 = MockModel(mock_name='#1', foo=1, bar='a')
        item_2 = MockModel(mock_name='#2', foo=1, bar='b')
        item_3 = MockModel(mock_name='#3', foo=3, bar='b')

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(~Q(foo=1) | Q(bar='a')))

        assert item_1 in results
        assert item_2 not in results
        assert item_3 in results

    def test_query_filters_items_by_q_object_and_with_one_empty(self):
        item_3 = MockModel(mock_name='#1', foo=3, bar='b')

        self.mock_set.add(item_3)
        results = list(self.mock_set.filter(Q(bar='b', foo=1)))

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

    def test_query_convert_to_pks(self):
        car1 = Car(id=101)
        car2 = Car(id=102)
        car3 = Car(id=103)

        old_cars = MockSet(car1, car2)
        all_cars = MockSet(car1, car2, car3)

        matches = all_cars.filter(pk__in=old_cars)

        self.assertEqual(list(old_cars), list(matches))

    def test_query_convert_values_list_to_pks(self):
        car1 = Car(id=101)
        car2 = Car(id=102)
        car3 = Car(id=103)

        old_cars = MockSet(car1, car2)
        old_car_pks = old_cars.values_list("pk", flat=True)
        all_cars = MockSet(car1, car2, car3)

        matches = all_cars.filter(pk__in=old_car_pks)

        self.assertEqual(list(old_cars), list(matches))

    def test_query_filters_model_objects_by_bad_field(self):
        item_1 = Car(speed=1)
        item_2 = Sedan(speed=2)
        item_3 = Car(speed=3)

        item_2.sedan = item_2

        self.mock_set.add(item_1, item_2, item_3)
        with self.assertRaisesRegex(
                FieldError,
                r"Cannot resolve keyword 'bad_field' into field\. "
                r"Choices are 'id', 'make', 'make_id', 'model', 'passengers', 'sedan', 'speed', 'variations'\."):
            self.mock_set.filter(bad_field='bogus')

    def test_query_filters_reverse_relationship_by_in_comparison(self):
        with mocked_relations(Manufacturer):
            cars = [Car(speed=1)]

            make = Manufacturer()
            make.car_set = MockSet(*cars)

            self.mock_set.add(make)

            result = self.mock_set.filter(car__speed__in=[1, 2])
            assert result.count() == 1

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

    def test_query_aggregate_on_related_field(self):
        with mocked_relations(Manufacturer):
            cars = [Car(speed=1), Car(speed=2), Car(speed=3)]

            make = Manufacturer()
            make.car_set = MockSet(*cars)

            self.mock_set.add(make)

            result = self.mock_set.aggregate(Avg('car__speed'))
            assert result['car__speed__avg'] == sum([c.speed for c in cars]) / len(cars)

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

    def test_query_aggregate_performs_array_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15),
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_ARRAY, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__array_agg'] == [x.foo for x in items]

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

    def test_query_latest_returns_the_last_element_from_ordered_set_using_fields_args(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.latest('foo')

        assert latest == item_3

    def test_query_latest_returns_the_last_element_from_ordered_set_using_field_name_kwarg(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.latest(field_name='foo')

        assert latest == item_3

    def test_query_latest_returns_the_last_element_from_ordered_set_using_meta_get_latest_by(self):
        item_1 = MagicMock(foo=1)
        item_2 = MagicMock(foo=2)
        item_3 = MagicMock(foo=3)

        objects = MockSet(item_3, item_1, item_2, model=MockModel())
        objects.model._meta.get_latest_by = 'foo'
        latest = objects.latest()

        assert latest == item_3

    def test_query_latest_raises_error_when_both_fields_args_and_field_name_kwarg_supplied(self):
        item_1 = MockModel(foo=1, bar='a')
        item_2 = MockModel(foo=2, bar='b')
        item_3 = MockModel(foo=3, bar='c')

        self.mock_set.add(item_3, item_1, item_2)

        self.assertRaises(ValueError, self.mock_set.latest, 'foo', field_name='bar')

    def test_query_latest_raises_error_when_no_fields_supplied(self):
        item_1 = MagicMock(foo=1)
        item_2 = MagicMock(foo=2)
        item_3 = MagicMock(foo=3)

        objects = MockSet(item_3, item_1, item_2, model=MockModel())

        self.assertRaises(ValueError, objects.latest)

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

    def test_query_order_by_random(self):
        def make_model(idx):
            return MockModel(
                mock_name='test{}'.format(idx),
                email='test{}@domain.com'.format(idx),
            )

        qs = MockSet(*[make_model(i) for i in range(10)])
        assert any(list(qs) != list(qs.order_by('?')) for _ in range(5))

    def test_ordered_queryset_pagination_does_not_raise_warning(self):
        item_1 = MockModel(foo=1, bar='a', mock_name='item_1')
        item_2 = MockModel(foo=1, bar='c', mock_name='item_2')
        item_3 = MockModel(foo=2, bar='b', mock_name='item_3')

        self.mock_set.add(item_1, item_3, item_2)

        qs = self.mock_set.order_by('foo', 'bar')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            Paginator(qs, 2)

            assert 0 == len(w)

    def test_query_distinct(self):
        item_1 = MockModel(foo=1, mock_name='item_1')
        item_2 = MockModel(foo=2, mock_name='item_2')
        item_3 = MockModel(foo=3, mock_name='item_3')

        self.mock_set.add(item_2, item_3, item_1, item_3)
        results = list(self.mock_set.distinct().order_by('foo'))

        assert results == [item_1, item_2, item_3], results

    def test_query_distinct_django_model(self):
        item_1 = Car(speed=1)
        item_2 = Car(speed=2)
        item_3 = Car(speed=3)

        self.mock_set.add(item_2, item_3, item_1, item_3)
        results = list(self.mock_set.distinct().order_by('speed'))

        assert results == [item_1, item_2, item_3], results

    def test_query_distinct_values(self):
        item_1 = MockModel(foo=1, mock_name='item_1')
        item_2 = MockModel(foo=2, mock_name='item_2')
        item_3 = MockModel(foo=3, mock_name='item_3')

        self.mock_set.add(item_2, item_3, item_1, item_3)
        results = list(self.mock_set.values('foo').distinct().order_by('foo'))

        expected = [
            {'foo': item_1.foo},
            {'foo': item_2.foo},
            {'foo': item_3.foo},
        ]
        assert results == expected, results

    def test_query_distinct_with_fields(self):
        item_1 = MockModel(foo=1, bar='c', foo_bar='x', mock_name='item_1')
        item_2 = MockModel(foo=2, bar='a', foo_bar='y', mock_name='item_2')
        item_3 = MockModel(foo=1, bar='c', foo_bar='z', mock_name='item_3')

        self.mock_set.add(item_2, item_3, item_1, item_3)
        results = list(self.mock_set.order_by('foo', 'bar', 'foo_bar').distinct('foo', 'bar'))

        assert results == [item_1, item_2], results

    def test_query_distinct_django_model_with_fields(self):
        item_1 = Car(speed=1, model='a')
        item_2 = Car(speed=2, model='b')
        item_3 = Car(speed=1, model='c')

        self.mock_set.add(item_2, item_3, item_1, item_3)
        results = list(self.mock_set.order_by('speed', 'model').distinct('speed'))

        assert results == [item_1, item_2], results

    def test_query_implements_iterator_on_items(self):
        items = [1, 2, 3]
        assert [x for x in MockSet(*items)] == items

    def test_query_creates_new_model_and_adds_to_set(self):
        qs = MockSet(model=create_model('foo', 'bar', 'none'))
        attrs = dict(foo=1, bar='a')
        obj = qs.create(**attrs)

        assert obj in [x for x in qs]
        assert hasattr(obj, 'foo') and obj.foo == 1
        assert hasattr(obj, 'bar') and obj.bar == 'a'
        assert hasattr(obj, 'none') and obj.none is None

    def test_query_create_raises_model_not_specified_when_mockset_model_is_none(self):
        qs = MockSet()
        attrs = dict(foo=1, bar='a')
        self.assertRaises(ModelNotSpecified, qs.create, **attrs)

    def test_query_create_raises_value_error_when_kwarg_key_is_not_in_concrete_fields(self):
        qs = MockSet(
            model=create_model('first', 'second', 'third')
        )
        attrs = dict(first=1, second=2, third=3, fourth=4)
        with self.assertRaises(FieldError):
            qs.create(**attrs)

    def test_query_update_returns_number_of_affected_rows(self):
        objects = [MockModel(foo=1), MockModel(foo=1), MockModel(foo=2)]
        qs = MockSet(*objects, model=create_model('foo', 'bar'))
        count = qs.filter(foo=1).update(bar=2)

        assert count == len(objects) - 1, count

    def test_query_update_with_multiple_values(self):
        objects = [MockModel(foo=1), MockModel(foo=2), MockModel(foo=3)]
        qs = MockSet(*objects, model=create_model('foo', 'bar'))

        set_foo, set_bar = 4, 5
        qs.update(foo=set_foo, bar=set_bar)

        for x in qs:
            assert x.foo == set_foo, x.foo
            assert x.bar == set_bar, x.bar

    def test_query_update_does_not_allow_related_model_fields(self):
        objects = [MockModel(foo=MockModel(bar=1)), MockModel(foo=MockModel(bar=2))]
        qs = MockSet(*objects, model=create_model('foo'))

        target = dict(foo__bar=2)
        with self.assertRaises(FieldError) as cm:
            qs.update(**target)

        assert 'Cannot update model field \'{}\''.format(next(iter(target))) in str(cm.exception)

    def test_query_delete_all_entries(self):
        item_1 = MockModel(foo=1, bar='a', mock_name='item_1')
        item_2 = MockModel(foo=1, bar='b', mock_name='item_2')

        self.mock_set.add(item_1, item_2)
        deleted_count, deleted_items = self.mock_set.delete()

        assert len(self.mock_set) == 0, len(self.mock_set)
        assert deleted_count == 2
        assert deleted_items == {'item_1': 1, 'item_2': 1}

    def test_query_delete_non_model_entries(self):
        items = [1, 2, 3, 'foo', 'bar', True]
        self.mock_set.add(*items)

        deleted_count, deleted_items = self.mock_set.delete()
        assert deleted_count == 6
        assert deleted_items == {'int': 3, 'str': 2, 'bool': 1}

    def test_query_delete_entries_propagated_from_nested_qs(self):
        item_1 = MockModel(foo=1, bar='a', mock_name='item_1')
        item_2 = MockModel(foo=1, bar='b', mock_name='item_2')

        self.mock_set.add(item_1, item_2)
        deleted_count, deleted_items = self.mock_set.filter(bar='b').delete()

        assert len(self.mock_set) == 1, len(self.mock_set)
        assert item_1 in self.mock_set
        assert item_2 not in self.mock_set
        assert deleted_count == 1
        assert deleted_items == {'item_2': 1}

    def test_query_gets_unique_match_by_attrs_from_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        result = self.mock_set.get(foo=2)

        assert item_2 == result

    def test_query_gets_unique_match_by_q_object(self):
        item_1 = MockModel(mock_name='#1', foo=1)
        item_2 = MockModel(mock_name='#2', foo=2)
        item_3 = MockModel(mock_name='#3', foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        assert self.mock_set.get(Q(foo=1)) == item_1

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

        self.mock_set = MockSet(item_1, item_2, item_3, model=Car)
        self.assertRaises(Car.DoesNotExist, self.mock_set.get, model='clowncar')

    def test_query_filter_keeps_class(self):
        item_1 = Car(model='battle')
        item_2 = Car(model='pious')
        item_3 = Car(model='hummus')

        self.mock_set = MockSet(item_1, item_2, item_3, model=Car)
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

        qs = MockSet(model=create_model('foo'))
        qs.add(item_1, item_2, item_3)
        obj, created = qs.get_or_create(foo=4)

        assert hasattr(obj, 'foo') and obj.foo == 4
        assert created is True

    def test_query_get_or_create_gets_existing_unique_match_with_defaults(self):
        qs = MockSet(
            model=create_model('first', 'second', 'third')
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
            model=create_model('first', 'second', 'third')
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
            model=create_model('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        obj, created = qs.get_or_create(defaults={'first': 3}, second=1)

        assert hasattr(obj, 'first') and obj.first == 3
        assert hasattr(obj, 'second') and obj.second == 1
        assert hasattr(obj, 'third') and obj.third is None
        assert created is True

    def test_query_get_or_create_raises_model_not_specified_with_defaults_when_mockset_model_is_none(self):
        qs = MockSet()
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        with self.assertRaises(ModelNotSpecified):
            qs.get_or_create(defaults={'first': 3, 'third': 2}, second=1)

    def test_query_update_or_create_gets_existing_unique_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_1, item_2, item_3)
        obj, created = self.mock_set.update_or_create(foo=2)

        assert obj == item_2
        assert created is False

    def test_query_update_or_create_raises_does_multiple_objects_returned_when_more_than_one_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=1)
        item_3 = MockModel(foo=2)

        self.mock_set.add(item_1, item_2, item_3)
        self.assertRaises(MultipleObjectsReturned, self.mock_set.update_or_create, foo=1)

    def test_query_update_or_create_creates_new_model_when_no_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        qs = MockSet(model=create_model('foo'))
        qs.add(item_1, item_2, item_3)
        obj, created = qs.update_or_create(foo=4)

        assert hasattr(obj, 'foo') and obj.foo == 4
        assert created is True

    def test_query_update_or_create_gets_existing_unique_match_with_defaults(self):
        qs = MockSet(
            model=create_model('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        obj, created = qs.update_or_create(defaults={'first': 3, 'third': 1}, second=2)

        assert hasattr(obj, 'second') and obj.second == 2
        assert created is False

    def test_query_update_or_create_raises_does_multiple_objects_returned_when_more_than_one_match_with_defaults(self):
        qs = MockSet(
            model=create_model('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(first=1)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        qs.add(item_1, item_2, item_3)
        with self.assertRaises(MultipleObjectsReturned):
            qs.update_or_create(first=1, defaults={'second': 2})

    def test_query_update_or_create_creates_new_model_when_no_match_with_defaults(self):
        qs = MockSet(
            model=create_model('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        obj, created = qs.update_or_create(defaults={'first': 3}, second=1)

        assert hasattr(obj, 'first') and obj.first == 3
        assert hasattr(obj, 'second') and obj.second == 1
        assert hasattr(obj, 'third') and obj.third is None
        assert created is True

    def test_query_update_or_create_updates_match_with_defaults(self):
        qs = MockSet(
            model=create_model('first', 'second', 'third')
        )
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        obj, created = qs.update_or_create(defaults={'first': 3, 'third': 1}, second=2)

        assert hasattr(obj, 'first') and obj.first == 3
        assert hasattr(obj, 'second') and obj.second == 2
        assert hasattr(obj, 'third') and obj.third == 1
        assert created is False

    def test_query_update_or_create_raises_model_not_specified_with_defaults_when_mockset_model_is_none(self):
        qs = MockSet()
        item_1 = MockModel(first=1)
        item_2 = MockModel(second=2)
        item_3 = MockModel(third=3)
        qs.add(item_1, item_2, item_3)

        with self.assertRaises(ModelNotSpecified):
            qs.update_or_create(defaults={'first': 3, 'third': 2}, second=1)

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
        qs = MockSet(MockModel(foo=1, bar=1), MockModel(foo=2, bar=2))
        self.assertRaises(TypeError, qs.values_list, 'foo', 'bar', flat=True)

    def test_query_values_list_raises_attribute_error_when_field_is_not_in_meta_concrete_fields(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(FieldError, qs.values_list, 'bar')

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

    def test_query_values_list_raises_type_error_if_flat_and_named_are_true(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(TypeError, qs.values_list, flat=True, named=True)

    def test_named_query_values_list(self):
        item_1 = MockModel(foo=1, bar=3)
        item_2 = MockModel(foo=2, bar=4)

        qs = MockSet(item_1, item_2)
        results_with_named_fields_fields = qs.values_list('foo', 'bar', named=True)
        assert results_with_named_fields_fields[0].foo == 1
        assert results_with_named_fields_fields[0].bar == 3
        assert results_with_named_fields_fields[1].foo == 2
        assert results_with_named_fields_fields[1].bar == 4

    def test_query_values_list_of_nested_field(self):
        with mocked_relations(Manufacturer, Car):
            make = Manufacturer(name='vw')
            self.mock_set.add(make)

            polo = Car(make=make, model='polo', speed=240)
            golf = Car(make=make, model='golf', speed=260)

            polo_white = CarVariation(car=polo, color='white')
            golf_white = CarVariation(car=golf, color='white')
            golf_black = CarVariation(car=golf, color='black')

            make.car_set = MockSet(polo, golf)
            polo.variations = MockSet(polo_white)
            golf.variations = MockSet(golf_white, golf_black)

            data = list(self.mock_set.values_list('name', 'car__model', 'car__variations__color'))

            assert (make.name, polo.model, polo_white.color) in data
            assert (make.name, golf.model, golf_black.color) in data

    def test_in_bulk(self):
        golf = Car(model='golf', id=1)
        polo = Car(model='polo', id=2)
        kia = Car(model='kia', id=4)
        qs = MockSet(golf, polo, kia)

        self.assertEqual(qs.in_bulk(), {1: golf, 2: polo, 4: kia})
        self.assertEqual(qs.in_bulk(id_list=['kia'], field_name='model'), {'kia': kia})

    def test_annotate(self):
        qs = MockSet(CarVariation(color='green', car=Car(model='golf', id=1), id=1),
                     CarVariation(color='red', car=Car(model='polo', id=2), id=2),
                     CarVariation(color=None, car=Car(model='kia', id=3), id=3),
                     )
        qs = qs.annotate(
            model=models.F('car__model'),
            str_value=models.Value('data', output_field=models.TextField()),
            bool_value=models.Value(True, output_field=models.BooleanField()),
            int_value=models.Value(10, output_field=models.IntegerField()),
            is_golf=models.Case(
                models.When(car__model='golf', then=True),
                default=False,
                output_field=models.BooleanField()
            ),
            color_or_car=Coalesce('color', models.F('car__model')),
        )

        values_res = list(qs.values('model', 'str_value', 'bool_value', 'int_value', 'is_golf', 'color_or_car'))
        self.assertEqual([
            {
                'model': 'golf',
                'int_value': 10,
                'str_value': 'data',
                'bool_value': True,
                'is_golf': True,
                'color_or_car': 'green'
            },
            {
                'model': 'polo',
                'int_value': 10,
                'str_value': 'data',
                'bool_value': True,
                'is_golf': False,
                'color_or_car': 'red'
            },
            {
                'model': 'kia',
                'int_value': 10,
                'str_value': 'data',
                'bool_value': True,
                'is_golf': False,
                'color_or_car': 'kia'
            },
        ], values_res)

        first = qs[0]
        self.assertEqual(first.model, 'golf')
        self.assertEqual(first.color_or_car, 'green')
        self.assertEqual(first.is_golf, True)
        self.assertEqual(first.int_value, 10)
        self.assertEqual(first.str_value, 'data')
        self.assertEqual(first.bool_value, True)

        second = qs[1]
        self.assertEqual(second.model, 'polo')
        self.assertEqual(second.color_or_car, 'red')
        self.assertEqual(second.is_golf, False)
        self.assertEqual(second.int_value, 10)
        self.assertEqual(second.str_value, 'data')
        self.assertEqual(second.bool_value, True)

        self.assertEqual(qs[2].color_or_car, 'kia')

    def test_annotate_returns_current_class_instance(self):
        class CustomMockSet(MockSet):
            pass

        qs = CustomMockSet(Car(model='golf', id=1))
        self.assertIsInstance(qs.annotate(model=models.F('model')), CustomMockSet)

    def test_query_values_raises_attribute_error_when_field_is_not_in_meta_concrete_fields(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        self.assertRaises(FieldError, qs.values, 'bar')

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

    def test_query_values_of_nested_field(self):
        with mocked_relations(Manufacturer, Car):
            make = Manufacturer(name='vw')
            self.mock_set.add(make)

            polo = Car(make=make, model='polo', speed=240)
            golf = Car(make=make, model='golf', speed=260)

            polo_white = CarVariation(car=polo, color='white')
            golf_white = CarVariation(car=golf, color='white')
            golf_black = CarVariation(car=golf, color='black')

            make.car_set = MockSet(polo, golf)
            polo.variations = MockSet(polo_white)
            golf.variations = MockSet(golf_white, golf_black)

            data = list(self.mock_set.values('car__model', 'car__variations__color', 'name'))
            assert {'name': make.name, 'car__model': polo.model, 'car__variations__color': polo_white.color} in data
            assert {'name': make.name, 'car__model': golf.model, 'car__variations__color': golf_white.color} in data
            assert {'name': make.name, 'car__model': golf.model, 'car__variations__color': golf_black.color} in data

    def test_query_length1(self):
        q = MockSet(MockModel())

        n = len(q)

        self.assertEqual(1, n)

    def test_query_length2(self):
        q = MockSet(MockModel(), MockModel())

        n = len(q)

        self.assertEqual(2, n)

    def test_query_create_model_raises_value_error_with_zero_arguments(self):
        with self.assertRaises(ValueError):
            create_model()

    def test_query_model_repr_returns_mock_name(self):
        model = MockModel(mock_name='model_name')
        assert repr(model) == model.mock_name

    def test_query_dates_year(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.date(2017, 1, 2))
        item2 = MockModel(date_begin=datetime.date(2017, 3, 12))
        item3 = MockModel(date_begin=datetime.date(2016, 3, 4))

        qs.add(item1, item2, item3)

        result = qs.dates('date_begin', 'year', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.date(2016, 1, 1)
        assert result[1] == datetime.date(2017, 1, 1)

        result = qs.dates('date_begin', 'year', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.date(2017, 1, 1)
        assert result[1] == datetime.date(2016, 1, 1)

    def test_query_dates_month(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.date(2017, 1, 2))
        item2 = MockModel(date_begin=datetime.date(2017, 1, 19))
        item3 = MockModel(date_begin=datetime.date(2017, 2, 4))
        qs.add(item1, item2, item3)

        result = qs.dates('date_begin', 'month', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.date(2017, 1, 1)
        assert result[1] == datetime.date(2017, 2, 1)

        result = qs.dates('date_begin', 'month', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.date(2017, 2, 1)
        assert result[1] == datetime.date(2017, 1, 1)

    def test_query_dates_day(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.date(2017, 1, 2))
        item2 = MockModel(date_begin=datetime.date(2017, 2, 14))
        item3 = MockModel(date_begin=datetime.date(2017, 2, 14))

        qs.add(item1, item2, item3)

        result = qs.dates('date_begin', 'day', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.date(2017, 1, 2)
        assert result[1] == datetime.date(2017, 2, 14)

        result = qs.dates('date_begin', 'day', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.date(2017, 2, 14)
        assert result[1] == datetime.date(2017, 1, 2)

    def test_query_datetimes_year(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.datetime(2017, 1, 2, 1, 2, 3))
        item2 = MockModel(date_begin=datetime.datetime(2017, 3, 12, 4, 5, 6))
        item3 = MockModel(date_begin=datetime.datetime(2016, 3, 4, 7, 8, 9))

        qs.add(item1, item2, item3)

        result = qs.datetimes('date_begin', 'year', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2016, 1, 1, 0, 0, 0)
        assert result[1] == datetime.datetime(2017, 1, 1, 0, 0, 0)

        result = qs.datetimes('date_begin', 'year', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert result[1] == datetime.datetime(2016, 1, 1, 0, 0, 0)

    def test_query_datetimes_month(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.datetime(2017, 1, 2, 1, 2, 3))
        item2 = MockModel(date_begin=datetime.datetime(2017, 1, 19, 4, 5, 6))
        item3 = MockModel(date_begin=datetime.datetime(2017, 2, 4, 7, 8, 9))
        qs.add(item1, item2, item3)

        result = qs.datetimes('date_begin', 'month', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 1, 0, 0, 0)
        assert result[1] == datetime.datetime(2017, 2, 1, 0, 0, 0)

        result = qs.datetimes('date_begin', 'month', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 2, 1, 0, 0, 0)
        assert result[1] == datetime.datetime(2017, 1, 1, 0, 0, 0)

    def test_query_datetimes_day(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.datetime(2017, 1, 2, 1, 2, 3))
        item2 = MockModel(date_begin=datetime.datetime(2017, 2, 14, 4, 5, 6))
        item3 = MockModel(date_begin=datetime.datetime(2017, 2, 14, 7, 8, 9))

        qs.add(item1, item2, item3)

        result = qs.datetimes('date_begin', 'day', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 2, 0, 0, 0)
        assert result[1] == datetime.datetime(2017, 2, 14, 0, 0, 0)

        result = qs.datetimes('date_begin', 'day', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 2, 14, 0, 0, 0)
        assert result[1] == datetime.datetime(2017, 1, 2, 0, 0, 0)

    def test_query_datetimes_hour(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 2, 3))
        item2 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 5, 6))
        item3 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 2, 8, 9))

        qs.add(item1, item2, item3)

        result = qs.datetimes('date_begin', 'hour', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 10, 1, 0, 0)
        assert result[1] == datetime.datetime(2017, 1, 10, 2, 0, 0)

        result = qs.datetimes('date_begin', 'hour', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 10, 2, 0, 0)
        assert result[1] == datetime.datetime(2017, 1, 10, 1, 0, 0)

    def test_query_datetimes_minute(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 2, 3))
        item2 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 2, 6))
        item3 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 3, 9))

        qs.add(item1, item2, item3)

        result = qs.datetimes('date_begin', 'minute', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 10, 1, 2, 0)
        assert result[1] == datetime.datetime(2017, 1, 10, 1, 3, 0)

        result = qs.datetimes('date_begin', 'minute', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 10, 1, 3, 0)
        assert result[1] == datetime.datetime(2017, 1, 10, 1, 2, 0)

    def test_query_datetimes_second(self):
        qs = MockSet(model=create_model('date_begin'))

        item1 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 2, 3))
        item2 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 2, 3))
        item3 = MockModel(date_begin=datetime.datetime(2017, 1, 10, 1, 2, 9))

        qs.add(item1, item2, item3)

        result = qs.datetimes('date_begin', 'second', 'ASC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 10, 1, 2, 3)
        assert result[1] == datetime.datetime(2017, 1, 10, 1, 2, 9)

        result = qs.datetimes('date_begin', 'second', 'DESC')

        assert len(result) == 2
        assert result[0] == datetime.datetime(2017, 1, 10, 1, 2, 9)
        assert result[1] == datetime.datetime(2017, 1, 10, 1, 2, 3)

    def test_empty_queryset_bool_converts_to_false(self):
        qs = MockSet()
        assert not bool(qs)

    def test_empty_queryset_filter(self):
        car1 = Car(id=101)
        car2 = Car(id=102)

        mockset = MockSet(car1, car2)
        self.assertEqual(mockset.count(), 2)
        self.assertEqual(mockset.filter(Q()).count(), 2)

    def test_mock_set_annotation_by_nested_mock_model(self):
        mockset = MockSet(
            MockModel(id=1, nested_mock=MockModel(id=1, field1="field_value"))
        )
        field1 = mockset.annotate(field1=models.F("nested_mock__field1")).values_list("field1")[0][0]
        assert field1 == "field_value"

    def test_set_replaces_all_items(self):
        mockset = MockSet(
            MockModel(id=1, field="value_1", mock_name="item1"),
            MockModel(id=2, field="value_2", mock_name="item2"),
        )
        mockset.set([MockModel(id=3, field="value_3", mock_name="item3")])

        assert len(mockset) == 1
        assert mockset[0].id == 3
