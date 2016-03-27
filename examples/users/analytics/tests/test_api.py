from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django_mock_queries.query import MockSet, MockModel
from mock import patch
from model_mommy import mommy

from examples.users.analytics.api import AnalyticsApi


class TestApi(TestCase):
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
