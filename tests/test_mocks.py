from django.db import connection
from django.db.utils import NotSupportedError
from django.db.backends.base.creation import BaseDatabaseCreation
from mock import patch
from unittest import TestCase

from django_mock_queries import mocks
from django_mock_queries.mocks import monkey_patch_test_db, mock_django_connection, ModelMocker
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

    def test_generic_model_mocker(self):
        with ModelMocker(Car):
            # New instance gets inserted
            obj = Car(speed=4)
            obj.save()
            self.assertEqual(Car.objects.get(pk=obj.id), obj)

            # Existing instance gets updated
            obj = Car(id=obj.id, speed=5)
            obj.save()
            self.assertEqual(Car.objects.get(pk=obj.id).speed, obj.speed)

            # Trying to update an instance that doesn't exists creates it
            obj = Car(id=123, speed=5)
            obj.save()
            self.assertEqual(Car.objects.get(pk=obj.id), obj)

    class CarModelMocker(ModelMocker):
        def validate_price(self):
            """ The real implementation would call an external service that
            we would like to skip but verify it's called before save. """

    def test_custom_model_mocker(self):
        with self.CarModelMocker(Car, 'validate_price') as mocker:
            obj = Car()
            obj.save()

            mocker.method('validate_price').assert_called_with()

    @CarModelMocker(Car, 'validate_price')
    def test_custom_model_mocker_callable(self, mocker):
        obj = Car()
        obj.save()

        mocker.method('validate_price').assert_called_with()
