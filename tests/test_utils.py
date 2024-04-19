from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from django_mock_queries import utils, constants


class TestUtils(TestCase):
    def test_merge_concatenates_lists(self):
        l1 = [1, 2, 3]
        l2 = [4, 5, 6]
        result = utils.merge(l1, l2)
        for x in (l1 + l2):
            assert x in result

    def test_merge_eliminates_duplicate_entries(self):
        l1 = [1, 2]
        l2 = [2, 3]
        result = utils.merge(l1, l2)
        for x in (l1 + l2):
            assert result.count(x) == 1

    def test_intersect_creates_list_with_common_elements(self):
        l1 = [1, 2]
        l2 = [2, 3]
        result = utils.intersect(l1, l2)
        for x in (l1 + l2):
            if x in l1 and x in l2:
                assert x in result
            else:
                assert x not in result

    def test_get_attribute_returns_value_with_default_comparison(self):
        obj = MagicMock(foo='test')
        value, comparison = utils.get_attribute(obj, 'foo')
        assert value == 'test'
        assert comparison is None

    def test_get_attribute_returns_false_when_value_is_false(self):
        obj = MagicMock(foo=False)
        value, comparison = utils.get_attribute(obj, 'foo')
        assert value is False
        assert comparison is None

    def test_get_attribute_returns_value_with_defined_comparison(self):
        obj = MagicMock(foo='test')
        value, comparison = utils.get_attribute(obj, 'foo__' + constants.COMPARISON_IEXACT)
        assert value == 'test'
        assert comparison == constants.COMPARISON_IEXACT

    def test_get_attribute_returns_none_with_isnull_comparison(self):
        obj = MagicMock(foo=None)
        value, comparison = utils.get_attribute(obj, 'foo__' + constants.COMPARISON_ISNULL)
        assert value is None
        assert comparison == constants.COMPARISON_ISNULL, comparison

    def test_get_attribute_returns_nested_object_value(self):
        obj = MagicMock(child=MagicMock(foo='test'))
        value, comparison = utils.get_attribute(obj, 'child__foo__' + constants.COMPARISON_IEXACT)
        assert value == 'test'
        assert comparison == constants.COMPARISON_IEXACT

    def test_get_attribute_returns_default_value_when_object_is_none(self):
        obj = None
        default_value = ''
        value, comparison = utils.get_attribute(obj, 'foo', default_value)
        assert value == default_value
        assert comparison is None

    def test_get_attribute_with_date(self):
        obj = MagicMock(foo=date(2017, 12, 31))
        value, comparison = utils.get_attribute(
            obj, 'foo__' + constants.COMPARISON_YEAR + '__' + constants.COMPARISON_GT
        )
        assert value == date(2017, 12, 31)
        assert comparison == (constants.COMPARISON_YEAR, constants.COMPARISON_GT)

    def test_get_attribute_returns_tuple_with_exact_as_default_comparison(self):
        obj = MagicMock(foo=datetime(2017, 1, 1))
        value, comparison = utils.get_attribute(obj, 'foo__' + constants.COMPARISON_YEAR)
        assert value == datetime(2017, 1, 1)
        assert comparison == (constants.COMPARISON_YEAR, constants.COMPARISON_EXACT)

    def test_validate_date_or_datetime_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, r'13 is incorrect value for month'):
            utils.validate_date_or_datetime(13, constants.COMPARISON_MONTH)

    def test_is_match_equality_check_when_comparison_none(self):
        result = utils.is_match(1, 1)
        assert result is True

        result = utils.is_match('a', 'a')
        assert result is True

        result = utils.is_match(1, '1')
        assert result is False

    def test_is_match_case_sensitive_equality_check(self):
        result = utils.is_match('a', 'A', constants.COMPARISON_EXACT)
        assert result is False

        result = utils.is_match('a', 'a', constants.COMPARISON_EXACT)
        assert result is True

    def test_is_match_case_insensitive_equality_check(self):
        result = utils.is_match('a', 'A', constants.COMPARISON_IEXACT)
        assert result is True

        result = utils.is_match('a', 'a', constants.COMPARISON_IEXACT)
        assert result is True

    def test_is_match_case_sensitive_contains_check(self):
        result = utils.is_match('abc', 'A', constants.COMPARISON_CONTAINS)
        assert result is False

        result = utils.is_match('abc', 'a', constants.COMPARISON_CONTAINS)
        assert result is True

    def test_is_match_case_list_contains_check(self):
        result = utils.is_match([1, 2, 3], [1, 2], constants.COMPARISON_CONTAINS)
        assert result is True

        result = utils.is_match([1, 2, 3], [1, 4], constants.COMPARISON_CONTAINS)
        assert result is False

        result = utils.is_match((1, 2, 3), (1, 2), constants.COMPARISON_CONTAINS)
        assert result is True

        result = utils.is_match((1, 2, 3), (1, 2, 3, 4), constants.COMPARISON_CONTAINS)
        assert result is False

    def test_is_match_case_insensitive_contains_check(self):
        result = utils.is_match('abc', 'A', constants.COMPARISON_ICONTAINS)
        assert result is True

        result = utils.is_match('abc', 'a', constants.COMPARISON_ICONTAINS)
        assert result is True

    def test_is_match_startswith_check(self):
        result = utils.is_match('abc', 'a', constants.COMPARISON_STARTSWITH)
        assert result is True

        result = utils.is_match('abc', 'A', constants.COMPARISON_STARTSWITH)
        assert result is False

    def test_is_match_istartswith_check(self):
        result = utils.is_match('abc', 'a', constants.COMPARISON_ISTARTSWITH)
        assert result is True

        result = utils.is_match('abc', 'A', constants.COMPARISON_ISTARTSWITH)
        assert result is True

    def test_is_match_endswith_check(self):
        result = utils.is_match('abc', 'c', constants.COMPARISON_ENDSWITH)
        assert result is True

        result = utils.is_match('abc', 'C', constants.COMPARISON_ENDSWITH)
        assert result is False

    def test_is_match_iendswith_check(self):
        result = utils.is_match('abc', 'c', constants.COMPARISON_IENDSWITH)
        assert result is True

        result = utils.is_match('abc', 'C', constants.COMPARISON_IENDSWITH)
        assert result is True

    def test_is_match_greater_than_value_check(self):
        result = utils.is_match(5, 3, constants.COMPARISON_GT)
        assert result is True

        result = utils.is_match(3, 5, constants.COMPARISON_GT)
        assert result is False

        result = utils.is_match(None, 5, constants.COMPARISON_GT)
        assert result is False

        result = utils.is_match(0, -2, constants.COMPARISON_GT)
        assert result is True

    def test_is_match_greater_than_equal_to_value_check(self):
        result = utils.is_match(5, 3, constants.COMPARISON_GTE)
        assert result is True

        result = utils.is_match(5, 5, constants.COMPARISON_GTE)
        assert result is True

        result = utils.is_match(3, 5, constants.COMPARISON_GTE)
        assert result is False

        result = utils.is_match(None, 5, constants.COMPARISON_GTE)
        assert result is False

    def test_is_match_less_than_value_check(self):
        result = utils.is_match(1, 2, constants.COMPARISON_LT)
        assert result is True

        result = utils.is_match(2, 2, constants.COMPARISON_LT)
        assert result is False

        result = utils.is_match(None, 5, constants.COMPARISON_LT)
        assert result is False

    def test_is_match_less_than_equal_to_value_check(self):
        result = utils.is_match(1, 2, constants.COMPARISON_LTE)
        assert result is True

        result = utils.is_match(1, 1, constants.COMPARISON_LTE)
        assert result is True

        result = utils.is_match(2, 1, constants.COMPARISON_LTE)
        assert result is False

        result = utils.is_match(None, 5, constants.COMPARISON_LTE)
        assert result is False

    def test_is_match_isnull_check(self):
        result = utils.is_match(1, True, constants.COMPARISON_ISNULL)
        assert result is False

        result = utils.is_match(1, False, constants.COMPARISON_ISNULL)
        assert result is True

        result = utils.is_match(None, True, constants.COMPARISON_ISNULL)
        assert result is True

        result = utils.is_match(None, False, constants.COMPARISON_ISNULL)
        assert result is False

        result = utils.is_match(None, 1, constants.COMPARISON_ISNULL)
        assert result is True

    def test_is_match_in_value_check(self):
        result = utils.is_match(2, [1, 3], constants.COMPARISON_IN)
        assert result is False

        result = utils.is_match(1, [1, 3], constants.COMPARISON_IN)
        assert result is True

        result = utils.is_match([3], [1, 2], constants.COMPARISON_IN)
        assert result is False

        result = utils.is_match([1, 3], [1, 2], constants.COMPARISON_IN)
        assert result is True

    @patch('django_mock_queries.utils.get_attribute')
    @patch('django_mock_queries.utils.is_match', MagicMock(return_value=True))
    def test_matches_includes_object_in_results_when_match(self, get_attr_mock):
        source = [
            MagicMock(foo=1),
            MagicMock(foo=2),
        ]

        get_attr_mock.return_value = None, None
        results = utils.matches(*source, foo__gt=0)

        for x in source:
            assert x in results

    @patch('django_mock_queries.utils.get_attribute')
    @patch('django_mock_queries.utils.is_match', MagicMock(return_value=False))
    def test_matches_excludes_object_from_results_when_not_match(self, get_attr_mock):
        source = [
            MagicMock(foo=1),
            MagicMock(foo=2),
        ]

        get_attr_mock.return_value = None, None
        results = utils.matches(*source, foo__gt=5)

        for x in source:
            assert x not in results

    def test_is_match_regex(self):
        result = utils.is_match('Monty Python 1234', r'M\w+\sPython\s\d+', constants.COMPARISON_REGEX)
        assert result is True

        result = utils.is_match('Monty Python 1234', r'm\w+\spython\s\d+', constants.COMPARISON_REGEX)
        assert result is False

        result = utils.is_match('Monty Python 1234', r'm\w+Holy Grail\s\d+', constants.COMPARISON_REGEX)
        assert result is False

    def test_is_match_iregex(self):
        result = utils.is_match('Monty Python 1234', r'M\w+\sPython\s\d+', constants.COMPARISON_IREGEX)
        assert result is True

        result = utils.is_match('Monty Python 1234', r'm\w+\spython\s\d+', constants.COMPARISON_IREGEX)
        assert result is True

        result = utils.is_match('Monty Python 1234', r'm\w+Holy Grail\s\d+', constants.COMPARISON_IREGEX)
        assert result is False

    def test_is_match_processes_datetime_field(self):
        result = utils.is_match(datetime(2017, 1, 1, 2, 3, 4), 1, (constants.COMPARISON_HOUR, constants.COMPARISON_LT))
        assert result is False

    def test_is_match_processes_date_field(self):
        result = utils.is_match(date(2017, 1, 1), 2016, (constants.COMPARISON_YEAR, constants.COMPARISON_GT))
        assert result is True

    def test_is_match_range_date_and_datetime(self):
        result = utils.is_match(date(2017, 1, 1), (date(2017, 1, 1), date(2017, 1, 2)), constants.COMPARISON_RANGE)
        assert result is True

        result = utils.is_match(
            datetime(2017, 1, 1, 0, 0, 0),
            (datetime(2017, 1, 1, 0, 0, 0), datetime(2017, 1, 1, 0, 0, 1)),
            constants.COMPARISON_RANGE
        )
        assert result is True

        result = utils.is_match(date(2017, 1, 1), (date(2017, 1, 2), date(2017, 1, 3)), constants.COMPARISON_RANGE)
        assert result is False

        result = utils.is_match(
            datetime(2015, 1, 1, 0, 0, 0),
            (datetime(2015, 1, 1, 0, 0, 1), datetime(2015, 1, 1, 0, 0, 2)),
            constants.COMPARISON_RANGE
        )
        assert result is False

    def test_is_match_range_numeric(self):
        result = utils.is_match(2, (2, 3), constants.COMPARISON_RANGE)
        assert result is True

        result = utils.is_match(1, (2, 3), constants.COMPARISON_RANGE)
        assert result is False

    def test_is_match_range_string(self):
        result = utils.is_match('b', ('b', 'c'), constants.COMPARISON_RANGE)
        assert result is True

        result = utils.is_match('a', ('b', 'c'), constants.COMPARISON_RANGE)
        assert result is False

    def test_is_match_overlap_string(self):
        result = utils.is_match(['a', 'b'], ['a', 'c'], constants.COMPARISON_OVERLAP)
        assert result is True

        result = utils.is_match(['a', 'b'], ['c', 'd'], constants.COMPARISON_OVERLAP)
        assert result is False

    def test_is_match_overlap_int(self):
        result = utils.is_match([1, 2], [1, 3], constants.COMPARISON_OVERLAP)
        assert result is True

        result = utils.is_match([1, 2], [3, 4], constants.COMPARISON_OVERLAP)
        assert result is False

    def test_matches_with_range(self):
        source = [
            MagicMock(foo=1),
            MagicMock(foo=3),
        ]

        results = utils.matches(*source, foo__range=(1, 2))
        assert source[0] in results
        assert source[1] not in results

    def test_is_match_with_overlap_strings(self):
        source = [
            MagicMock(foo=['abc', 'def', 'ghi']),
            MagicMock(foo=['jkl', 'mno', 'pqr']),
        ]

        results = utils.matches(*source, foo__overlap=["abc", "xyz"])
        assert source[0] in results
        assert source[1] not in results

    def test_is_like_date_or_datetime_for_datetime_obj(self):
        result = utils.is_like_date_or_datetime(date(2019, 1, 1))
        assert result is True

    def test_is_like_date_or_datetime_for_date_obj(self):
        result = utils.is_like_date_or_datetime(datetime(2019, 1, 1))
        assert result is True

    def test_is_like_date_or_datetime_for_non_date_or_datetime_obj(self):
        result = utils.is_like_date_or_datetime('non_datetime_obj')
        assert result is False

    def test_get_field_value_returns_dict_value(self):
        dict_obj = {'key': 45}
        result = utils.get_field_value(dict_obj, 'key')
        assert result == 45

    def test_get_field_value_returns_datetime_obj(self):
        datetime_obj = datetime(2019, 1, 2)
        result = utils.get_field_value(datetime_obj, 'date')
        assert result == datetime_obj

    def test_get_field_value_returns_date_obj(self):
        date_obj = date(2019, 1, 2)
        result = utils.get_field_value(date_obj, 'date')
        assert result == date_obj
