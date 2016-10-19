from mock import MagicMock, ANY
from unittest import TestCase

from django_mock_queries.constants import *
from django_mock_queries.exceptions import ModelNotSpecified
from django_mock_queries.query import MockSet, MockModel


class TestQuery(TestCase):
    def setUp(self):
        self.mock_set = MockSet()

    def test_query_counts_items_in_set(self):
        items = [1, 2, 3]
        assert MockSet(*items).count() == len(items)

    def test_query_project_returns_whole_item_by_index(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)

        qs = MockSet(item_1, item_2)
        assert qs.project(1) == item_2

    def test_query_project_returns_item_flat_attribute(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)

        qs = MockSet(item_1, item_2)
        qs.flat = True
        qs.projection = ['foo']

        assert qs.project(1) == item_2.foo

    def test_query_project_returns_item_specified_attributes_tuple(self):
        item_1 = MockModel(foo=1, bar='a')
        item_2 = MockModel(foo=2, bar='b')

        qs = MockSet(item_1, item_2)
        qs.flat = False
        qs.projection = ['foo', 'bar']

        attrs = qs.project(1)
        assert attrs[0] == item_2.foo
        assert attrs[1] == item_2.bar

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

        source = [item_1, item_2, item_3]
        query = MagicMock(connector=CONNECTORS_OR, children=[('foo', 1), ('foo', 2)])
        results = self.mock_set.filter_q(source, query)

        assert item_1 in results
        assert item_2 in results
        assert item_3 not in results

    def test_query_filters_items_by_q_object_and(self):
        item_1 = MockModel(mock_name='#1', foo=1, bar='a')
        item_2 = MockModel(mock_name='#2', foo=1, bar='b')
        item_3 = MockModel(mock_name='#3', foo=3, bar='b')

        source = [item_1, item_2, item_3]
        query = MagicMock(connector=CONNECTORS_AND, children=[('foo', 1), ('bar', 'b')])
        results = self.mock_set.filter_q(source, query)

        assert item_1 not in results
        assert item_2 in results
        assert item_3 not in results

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
            MockModel(foo=15)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_SUM, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__sum'] == sum([x.foo for x in items])

    def test_query_aggregate_performs_count_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_COUNT, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__count'] == len(items)

    def test_query_aggregate_performs_max_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_MAX, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__max'] == max([x.foo for x in items])

    def test_query_aggregate_performs_min_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_MIN, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__min'] == min([x.foo for x in items])

    def test_query_aggregate_performs_avg_on_queryset_field(self):
        items = [
            MockModel(foo=5),
            MockModel(foo=10),
            MockModel(foo=15)
        ]
        self.mock_set.add(*items)

        expr = MagicMock(function=AGGREGATES_AVG, source_expressions=[MockModel(name='foo')])
        result = self.mock_set.aggregate(expr)

        assert result['foo__avg'] == sum([x.foo for x in items]) / len(items)

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
        self.assertRaises(Exception, self.mock_set.latest, 'foo')

    def test_query_earliest_returns_the_first_element_from_ordered_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.earliest('foo')

        assert latest == item_1

    def test_query_earliest_raises_error_exist_when_empty_set(self):
        self.mock_set.clear()
        self.assertRaises(Exception, self.mock_set.earliest, 'foo')

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
        self.assertRaises(Exception, self.mock_set.get, foo=4)

    def test_query_get_raises_does_multiple_objects_returned_when_more_than_one_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=1)
        item_3 = MockModel(foo=2)

        self.mock_set.add(item_1, item_2, item_3)
        self.assertRaises(Exception, self.mock_set.get, foo=1)

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
        self.assertRaises(Exception, self.mock_set.get_or_create, foo=1)

    def test_query_get_or_create_creates_new_model_when_no_match(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        qs = MockSet(cls=MockModel)
        qs.add(item_1, item_2, item_3)
        obj, created = qs.get_or_create(foo=4)

        assert hasattr(obj, 'foo') and obj.foo == 4
        assert created is True

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

    def test_query_values_list_returns_qs_clone_with_flat_and_projection_fields_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)

        qs = MockSet(item_1, item_2)
        projection = ('foo',)
        obj = qs.values_list(*projection, flat=True)

        assert obj.flat is True
        assert obj.projection == projection
