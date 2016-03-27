from django.test import TestCase
from django_mock_queries.query import MockModel
from mock import patch

from examples.users.analytics import views


class TestViews(TestCase):
    @patch('examples.users.analytics.api.AnalyticsApi.active_users')
    def test_views_active_users_contains_usernames_separated_by_comma(self, active_users_mock):
        users = []
        for i in range(5):
            users.append(MockModel(username='user_%d' % i))

        active_users_mock.return_value = users
        response = views.active_users()

        expected = ', '.join([x.username for x in users])
        self.assertEqual(response.content, expected)
