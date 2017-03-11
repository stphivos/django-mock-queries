""" Example of mocking the database and using django_mock_queries.

There are two kinds of test cases here: TestApi is a regular Django
test that uses the database. The others use MockSet and mocked_relations
to simulate QuerySets in memory, so they're much faster than regular Django
tests. You can even run them without creating a database by using the
settings_mocked module.
./manage.py test --settings=users.settings_mocked
The regular tests can't run without the database, so make them skip
if the database is mocked. Use this decorator:
@skipIfDBFeature('is_mocked')
"""

from datetime import date, timedelta

from django_mock_queries.query import MockModel
from django_mock_queries.mocks import mocked_relations
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


@mocked_relations(User)
class TestViews(TestCase):
    def test_views_active_users_contains_usernames_separated_by_comma(self):
        for i in range(5):
            User.objects.add(MockModel(username='user_%d' % i,
                                       is_active=True))

        response = views.active_users()

        expected = ', '.join([x.username for x in User.objects.all()])
        self.assertEqual(expected, response.content.decode('utf-8'))


@mocked_relations(User)
class TestMockedApi(TestCase):
    def setUp(self):
        self.api = AnalyticsApi()

    def test_api_active_users_filters_by_is_active_true(self):
        active_user = MockModel(mock_name='active user', is_active=True)
        inactive_user = MockModel(mock_name='inactive user', is_active=False)

        User.objects.add(*[active_user, inactive_user])
        results = [x for x in self.api.active_users()]

        assert active_user in results
        assert inactive_user not in results

    def test_api_create_user(self):
        attrs = dict((k, v) for (k, v) in mommy.prepare(User).__dict__.items() if k[0] != '_')
        user = self.api.create_user(**attrs)
        assert isinstance(user, User)

        for k, v in attrs.items():
            assert getattr(user, k) == v

        # noinspection PyUnresolvedReferences
        assert User.save.call_count == 1

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
        User.objects.add(*(past_visitors + today_visitors))
        count = self.api.today_visitors_count()
        assert count == len(today_visitors)
        assert User.objects.filter(last_login__year__lte=2017).exists() is True
        assert User.objects.filter(last_login__year__gt=2018).exists() is False


# Comment out this decorator to see what happens when you forget to
# mock some database access. It should work under "./manage.py test", but
# raise a helpful error when run with "--settings=users.settings_mocked".
@mocked_relations(User)
class TestMockedUser(TestCase):
    def test_create(self):
        start_count = User.objects.count()

        User.objects.create(username='bob')
        final_count = User.objects.count()

        self.assertEqual(start_count+1, final_count)
