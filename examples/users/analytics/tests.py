""" Example of mocking the database and using django_mock_queries.

There are two kinds of test cases here: TestApi is a regular Django
test that uses the database. TestViews and TestMockedApi use MockSet
to simulate QuerySets in memory, so they're much faster than regular Django
tests. You can even run them without creating a database by using the
settings_mocked module.
./manage.py test --settings=users.settings_mocked
The regular tests can't run without the database, so make them skip
if the database is mocked. Use this decorator:
@skipIfDBFeature('is_mocked')
"""

from datetime import date, timedelta
from mock import patch

from django_mock_queries.query import MockSet, MockModel
from django.contrib.auth.models import User
from django.test import TestCase, skipIfDBFeature
from model_mommy import mommy
from analytics.api import AnalyticsApi
from analytics import views


@skipIfDBFeature('is_mocked')
class TestApi(TestCase):
    def test_create(self):
        start_count = User.objects.count()

        User.objects.create(username='bob')
        final_count = User.objects.count()

        self.assertEqual(start_count+1, final_count)


class TestViews(TestCase):
    @patch('analytics.api.AnalyticsApi.active_users')
    def test_views_active_users_contains_usernames_separated_by_comma(self, active_users_mock):
        mock_users = []
        for i in range(5):
            mock_users.append(MockModel(username='user_%d' % i))

        active_users_mock.return_value = mock_users
        response = views.active_users()

        expected = ', '.join([x.username for x in mock_users])
        self.assertEqual(expected, response.content.decode('utf-8'))


class TestMockedApi(TestCase):
    users = MockSet(cls=User)
    user_save = patch('django.contrib.auth.models.User.save')
    user_objects = patch('django.contrib.auth.models.User.objects', users)

    def setUp(self):
        self.api = AnalyticsApi()
        self.users.clear()

    @user_objects
    def test_api_active_users_filters_by_is_active_true(self):
        active_user = MockModel(mock_name='active user', is_active=True)
        inactive_user = MockModel(mock_name='inactive user', is_active=False)

        self.users.add(*[active_user, inactive_user])
        results = [x for x in self.api.active_users()]

        assert active_user in results
        assert inactive_user not in results

    @user_save
    @user_objects
    def test_api_create_user(self, save_mock):
        attrs = dict((k, v) for (k, v) in mommy.prepare(User).__dict__.items() if k[0] != '_')
        user = self.api.create_user(**attrs)
        assert isinstance(user, User)

        for k, v in attrs.items():
            assert getattr(user, k) == v

        assert save_mock.call_count == 1

    @user_objects
    def test_api_today_visitors_counts_todays_logins(self):
        past_visitors = [
            MockModel(last_login=(date.today() - timedelta(days=1))),
            MockModel(last_login=(date.today() - timedelta(days=2))),
            MockModel(last_login=(date.today() - timedelta(days=3))),
        ]
        today_visitors = [
            MockModel(last_login=date.today()),
            MockModel(last_login=date.today())
        ]
        self.users.add(*(past_visitors + today_visitors))
        count = self.api.today_visitors_count()
        assert count == len(today_visitors)

    # Comment out these two decorators to see what happens when you forget to
    # mock some database access. It should work under "./manage.py test", but
    # raise a helpful error when run with "--settings=users.settings_mocked".
    # noinspection PyUnusedLocal
    @user_save
    @user_objects
    def test_create(self, save_mock=None):
        start_count = User.objects.count()

        User.objects.create(username='bob')
        final_count = User.objects.count()

        self.assertEqual(start_count+1, final_count)
