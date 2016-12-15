from django.db import connection
from django.db.utils import NotSupportedError
from django.db.backends.base.creation import BaseDatabaseCreation
from django_mock_queries.mocks import monkey_patch_test_db, mock_django_connection
from mock import patch
from unittest import TestCase

from django_mock_queries import mocks
from tests.mock_models import Car


class TestMocks(TestCase):
    def test_mock_sql_raises_error(self):
        """ Get a clear error if you forget to mock a database query. """
        with self.assertRaisesRegexp(
                NotSupportedError,
                "Mock database tried to execute SQL for Car model."):
            Car.objects.count()

    def test_mock_django_setup_called_again(self):
        """ Shouldn't do anything the second time you call. """
        mocks.mock_django_setup('tests.mock_settings')

    # noinspection PyUnresolvedReferences
    @patch('django_mock_queries.mocks.mock_django_connection')
    @patch.multiple('django.db.backends.base.creation.BaseDatabaseCreation',
                    create_test_db=None,
                    destroy_test_db=None)
    def test_monkey_patch_test_db(self, mock_method):
        monkey_patch_test_db()

        creation = BaseDatabaseCreation(None)
        creation.create_test_db()
        creation.destroy_test_db('foo_db')

        mock_method.assert_called_once_with(None)

    # noinspection PyUnusedLocal
    @patch('django.db.utils.ConnectionHandler')
    def test_mock_django_connection(self, mock_handler):
        is_foo_before = bool(getattr(connection.features, 'is_foo', False))

        mock_django_connection(disabled_features=['is_foo'])

        is_foo_after = bool(getattr(connection.features, 'is_foo', False))

        self.assertTrue(is_foo_before)
        self.assertFalse(is_foo_after)
