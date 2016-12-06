""" Example of standard Django tests.

Think of these as integration tests that require a database to run.
You want to run them regularly, but maybe not as often as the pure
unit tests in tests_mock.py, because the database access slows them down.
"""


from django.contrib.auth.models import User
from django.test import TestCase


class TestApi(TestCase):
    def test_create(self):
        start_count = User.objects.count()

        User.objects.create(username='bob')
        final_count = User.objects.count()

        self.assertEqual(start_count+1, final_count)
