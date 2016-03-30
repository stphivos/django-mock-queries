from mock import MagicMock
from unittest import TestCase

from django_mock_queries.query import MockSet


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
        item_1 = MagicMock(foo=1)
        item_2 = MagicMock(foo=2)

        self.mock_set.add(item_1, item_2)
        self.mock_set.remove(foo=1)

        assert item_1 not in list(self.mock_set)
        assert item_2 in list(self.mock_set)

    def test_query_filters_items_by_attributes(self):
        item_1 = MagicMock(foo=1, bar='a')
        item_2 = MagicMock(foo=1, bar='b')
        item_3 = MagicMock(foo=2, bar='b')

        self.mock_set.add(item_1, item_2, item_3)
        results = list(self.mock_set.filter(foo=1, bar='b'))

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
        item_1 = MagicMock(foo=1)
        item_2 = MagicMock(foo=2)
        item_3 = MagicMock(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.latest('foo')

        assert latest == item_3

    def test_query_earliest_returns_the_first_element_from_ordered_set(self):
        item_1 = MagicMock(foo=1)
        item_2 = MagicMock(foo=2)
        item_3 = MagicMock(foo=3)

        self.mock_set.add(item_3, item_1, item_2)
        latest = self.mock_set.earliest('foo')

        assert latest == item_1

    def test_query_implements_iterator_on_items(self):
        items = [1, 2, 3]
        assert [x for x in MockSet(*items)] == items
