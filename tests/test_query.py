from mock import MagicMock
from unittest import TestCase

from django_mock_queries.constants import CONNECTORS_OR, CONNECTORS_AND
from django_mock_queries.query import MockSet, MockModel


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

    def test_query_latest_returns_the_last_element_from_ordered_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.latest('foo')

        assert latest == item_3

    def test_query_earliest_returns_the_first_element_from_ordered_set(self):
        item_1 = MockModel(foo=1)
        item_2 = MockModel(foo=2)
        item_3 = MockModel(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.earliest('foo')

        assert latest == item_1

    def test_query_implements_iterator_on_items(self):
        items = [1, 2, 3]
        assert [x for x in MockSet(*items)] == items

    def test_query_return_self_methods_accept_any_parameters_and_return_instance(self):
        qs = MockSet(MockModel(foo=1), MockModel(foo=2))
        assert qs == qs.all()
        assert qs == qs.only('f1')
        assert qs == qs.defer('f2', 'f3')
        assert qs == qs.using('default')
        assert qs == qs.select_related('t1', 't2')
        assert qs == qs.prefetch_related('t3', 't4')
        assert qs == qs.select_for_update()
