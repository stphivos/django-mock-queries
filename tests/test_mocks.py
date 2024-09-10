from unittest import TestCase
from unittest.mock import patch, MagicMock, PropertyMock

import django
from django.db import connection
from django.db.utils import NotSupportedError
from django.db.backends.base.creation import BaseDatabaseCreation

from django_mock_queries import mocks
from django_mock_queries.mocks import monkey_patch_test_db, mock_django_connection, \
    MockOneToOneMap, MockOneToManyMap, PatcherChain, mocked_relations, ModelMocker, Mocker
from django_mock_queries.query import MockSet
from tests.mock_models import Car, Sedan, Manufacturer, CarVariation


class TestMocks(TestCase):
    def test_mock_sql_raises_error(self):
        """ Get a clear error if you forget to mock a database query. """
        with self.assertRaisesRegex(
                NotSupportedError,
                "Mock database tried to execute SQL for Car model."):
            Car.objects.count()

    def test_exists_raises_error(self):
        """ Get a clear error if you forget to mock a database query. """
        with self.assertRaisesRegex(
                NotSupportedError,
                "Mock database tried to execute SQL for Car model."):
            Car.objects.exists()

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


# noinspection PyUnresolvedReferences,PyStatementEffect
class MockOneToOneTests(TestCase):
    def test_not_mocked(self):
        car = Car(id=99)

        with self.assertRaises(NotSupportedError):
            car.sedan

    @patch.object(Car, 'sedan', MockOneToOneMap(Car.sedan))
    def test_not_set(self):
        car = Car(id=99)

        with self.assertRaises(Car.sedan.RelatedObjectDoesNotExist):
            car.sedan

    @patch.object(Car, 'sedan', MockOneToOneMap(Car.sedan))
    def test_set(self):
        car = Car()
        sedan = Sedan()
        car.sedan = sedan

        self.assertIs(car.sedan, sedan)

    @patch.object(Car, 'sedan', MockOneToOneMap(Car.sedan))
    def test_set_on_individual_object(self):
        car = Car()
        car2 = Car()
        car.sedan = Sedan()

        with self.assertRaises(Car.sedan.RelatedObjectDoesNotExist):
            car2.sedan

    @patch.object(Car, 'sedan', MockOneToOneMap(Car.sedan))
    def test_delegation(self):
        if django.VERSION[0] < 2:
            self.assertEqual(Car.sedan.cache_name, '_sedan_cache')
        else:
            """ TODO - Refactored internal fields value cache: """
            # https://github.com/django/django/commit/bfb746f983aa741afa3709794e70f1e0ab6040b5#diff-507b415116b409afa4f723e41a759a9e


# noinspection PyUnresolvedReferences,PyStatementEffect
class MockOneToManyTests(TestCase):
    def test_not_mocked(self):
        m = Manufacturer(id=99)

        with self.assertRaisesRegex(
                NotSupportedError,
                'Mock database tried to execute SQL for Car model'):
            m.car_set.count()

    def test_mock_is_removed(self):
        m = Manufacturer(id=99)

        with patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set)):
            m.car_set = MockSet(Car(speed=95))
            self.assertEqual(1, m.car_set.count())

        with self.assertRaisesRegex(
                NotSupportedError,
                'Mock database tried to execute SQL for Car model'):
            m.car_set.count()

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    def test_not_set(self):
        m = Manufacturer()

        self.assertEqual(0, m.car_set.count())

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    def test_set(self):
        m = Manufacturer()
        car_1 = Car(speed=95)
        car_2 = Car(speed=40)
        m.car_set.add(car_1)
        m.car_set.add(car_2)

        self.assertIs(m.car_set.first(), car_1)
        self.assertEqual(list(m.car_set.all()), [car_1, car_2])

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    def test_set_on_individual_object(self):
        m = Manufacturer()
        m.car_set.add(Car(speed=95))
        m2 = Manufacturer()

        self.assertEqual(0, m2.car_set.count())

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    def test_set_explicit_collection(self):
        m = Manufacturer()
        m.car_set.add(Car(speed=95))

        car = Car(speed=100)
        m.car_set = MockSet(car)

        self.assertIs(m.car_set.first(), car)

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    @patch.object(Car, 'save', MagicMock)
    def test_create(self):
        m = Manufacturer()
        car = m.car_set.create(speed=95)

        self.assertIsInstance(car, Car)
        self.assertEqual(95, car.speed)

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    def test_delegation(self):
        """ We can still access fields from the original relation manager. """
        self.assertTrue(Manufacturer.car_set.related_manager_cls.do_not_call_in_templates)

    @patch.object(Manufacturer, 'car_set', MockOneToManyMap(Manufacturer.car_set))
    def test_raises(self):
        """ Raises an error specific to the child class. """
        m = Manufacturer()

        with self.assertRaises(Car.DoesNotExist):
            m.car_set.get(speed=0)


# noinspection PyUnusedLocal
def zero_sum(items):
    return 0


class PatcherChainTest(TestCase):
    patch_mock_max = patch('builtins.max')
    patch_zero_sum = patch('builtins.sum', zero_sum)

    @patch_zero_sum
    def test_patch_dummy(self):
        sum_result = sum([1, 2, 3])

        self.assertEqual(0, sum_result)

    @patch_mock_max
    def test_patch_mock(self, mock_max):
        mock_max.return_value = 42
        max_result = max([1, 2, 3])

        self.assertEqual(42, max_result)

    @PatcherChain([patch_zero_sum, patch_mock_max])
    def test_patch_both(self, mock_max):
        sum_result = sum([1, 2, 3])
        mock_max.return_value = 42
        max_result = max([1, 2, 3])

        self.assertEqual(0, sum_result)
        self.assertEqual(42, max_result)

    @PatcherChain([patch_mock_max, patch_zero_sum])
    def test_patch_both_reversed(self, mock_max):
        sum_result = sum([1, 2, 3])
        mock_max.return_value = 42
        max_result = max([1, 2, 3])

        self.assertEqual(0, sum_result)
        self.assertEqual(42, max_result)

    @PatcherChain([patch_mock_max], pass_mocks=False)
    def test_mocks_not_passed(self):
        """ Create a new mock, but don't pass it to the test method. """

    def test_context_manager(self):
        with PatcherChain([PatcherChainTest.patch_mock_max,
                           PatcherChainTest.patch_zero_sum]) as mocked:
            sum_result = sum([1, 2, 3])
            mocked[0].return_value = 42
            max_result = max([1, 2, 3])

            self.assertEqual(0, sum_result)
            self.assertEqual(42, max_result)
            self.assertEqual(2, len(mocked))
            self.assertIs(zero_sum, mocked[1])

    def test_start(self):
        patcher = PatcherChain([PatcherChainTest.patch_mock_max,
                                PatcherChainTest.patch_zero_sum])
        mocked = patcher.start()
        self.addCleanup(patcher.stop)

        sum_result = sum([1, 2, 3])
        mocked[0].return_value = 42
        max_result = max([1, 2, 3])

        self.assertEqual(0, sum_result)
        self.assertEqual(42, max_result)
        self.assertEqual(2, len(mocked))
        self.assertIs(zero_sum, mocked[1])


@PatcherChain([patch('builtins.max'), patch('builtins.sum', zero_sum)],
              pass_mocks=False)
class PatcherChainOnClassTest(TestCase):
    test_example_attribute = 42

    def test_patch_dummy(self):
        sum_result = sum([1, 2, 3])

        self.assertEqual(0, sum_result)

    def test_patch_mock(self):
        max_result = max([1, 2, 3])

        self.assertIsInstance(max_result, MagicMock)

    def test_patch_both(self):
        sum_result = sum([1, 2, 3])
        max_result = max([1, 2, 3])

        self.assertEqual(0, sum_result)
        self.assertIsInstance(max_result, MagicMock)

    def test_attribute(self):
        self.assertEqual(42, PatcherChainOnClassTest.test_example_attribute)


class MockedRelationsTest(TestCase):
    @mocked_relations(Manufacturer)
    def test_mocked_relations_decorator(self):
        m = Manufacturer()

        self.assertEqual(0, m.car_set.count())
        m.car_set.add(Car())
        self.assertEqual(1, m.car_set.count())

    def test_mocked_relations_context_manager(self):
        m = Manufacturer()

        with mocked_relations(Manufacturer):
            self.assertEqual(0, m.car_set.count())
            m.car_set.add(Car())
            self.assertEqual(1, m.car_set.count())

    def test_mocked_relations_reusing_patcher(self):
        patcher = mocked_relations(Manufacturer)
        with patcher:
            self.assertEqual(0, Manufacturer.objects.count())
            Manufacturer.objects.add(Manufacturer())
            self.assertEqual(1, Manufacturer.objects.count())

        with patcher:
            self.assertEqual(0, Manufacturer.objects.count())
            Manufacturer.objects.add(Manufacturer())
            self.assertEqual(1, Manufacturer.objects.count())

    @mocked_relations(Manufacturer)
    def test_mocked_relations_with_garbage_collection(self):
        self.longMessage = True
        for group_index in range(10):
            m = Manufacturer()
            self.assertEqual(0,
                             m.car_set.count(),
                             'group_index: {}'.format(group_index))
            m.car_set.add(Car())
            self.assertEqual(1, m.car_set.count())
            del m

    def test_mocked_relations_replaces_other_mocks(self):
        original_type = type(Manufacturer.car_set)
        self.assertIsInstance(Manufacturer.car_set, original_type)

        with mocked_relations(Manufacturer):
            Manufacturer.car_set = PropertyMock('Manufacturer.car_set')

        self.assertIsInstance(Manufacturer.car_set, original_type)

    @mocked_relations(Sedan)
    def test_mocked_relations_parent(self):
        sedan = Sedan(speed=95)

        self.assertEqual(0, sedan.passengers.count())

    @mocked_relations(Sedan)
    def test_mocked_relations_mock_twice(self):
        """ Don't reset the mocking if a class is mocked twice.

        Could happen where Sedan is mocked on the class, and Car (the base
        class) is mocked on a method.
        """
        Car.objects.add(Car(speed=95))
        self.assertEqual(1, Car.objects.count())

        with mocked_relations(Car):
            self.assertEqual(1, Car.objects.count())

    @mocked_relations(Manufacturer)
    def test_mocked_relations_raises_specific_error(self):
        with self.assertRaises(Manufacturer.DoesNotExist):
            Manufacturer.objects.get(name='sam')

    @mocked_relations(Manufacturer, Car)
    def test_mocked_relations_is_match_in_children(self):
        car = Car()
        manufacturer = Manufacturer()
        manufacturer.car_set.add(car)
        Manufacturer.objects.add(manufacturer)

        car_manufacturers = Manufacturer.objects.filter(car=car)

        self.assertEqual([manufacturer], list(car_manufacturers))

    @mocked_relations(Manufacturer, Car)
    def test_mocked_relations_create_foreign_key_with_kwargs(self):
        make = Manufacturer.objects.create(name='foo')
        Car.objects.create(make=make)


class TestMockers(TestCase):
    class CarModelMocker(ModelMocker):
        def validate_price(self):
            """ The real implementation would call an external service that
            we would like to skip but verify it's called before save. """

    def test_mocker_with_replacement_method(self):
        class Foo(object):
            def who(self):
                return 'foo'

        class Bar(Mocker):
            def who(self):
                return 'bar'

        with Bar(Foo, 'who') as mocker:
            self.assertEqual(Foo().who(), mocker.who())

    def test_mocker_with_replacement_attribute(self):
        class Foo(object):
            who = 'foo'

        class Bar(Mocker):
            who = 'bar'

        with Bar(Foo, 'who') as mocker:
            self.assertEqual(Foo.who, mocker.who)

    def test_mocker_without_replacement(self):
        class Foo(object):
            def who(self):
                return 'foo'

        class Bar(Mocker):
            pass

        with Bar(Foo, 'who'):
            self.assertIsInstance(Foo().who, MagicMock)

    def test_model_mocker_instance_save(self):
        with ModelMocker(Car):
            # New instance gets inserted
            obj = Car(speed=4)
            obj.save()
            self.assertEqual(Car.objects.get(pk=obj.id), obj)

            # Another instances gets inserted and has a different ID
            obj2 = Car(speed=5)
            obj.save()
            self.assertNotEqual(obj.id, obj2.id)

            # Existing instance gets updated
            obj = Car(id=obj.id, speed=5)
            obj.save()
            self.assertEqual(Car.objects.get(pk=obj.id).speed, obj.speed)

            # Trying to update an instance that doesn't exists creates it
            obj = Car(id=123, speed=5)
            obj.save()
            self.assertEqual(Car.objects.get(pk=obj.id), obj)

    def test_model_mocker_objects_create(self):
        with ModelMocker(Car):
            obj = Car.objects.create(speed=10)
            self.assertEqual(Car.objects.get(pk=obj.id), obj)

    def test_model_mocker_update_fk_from_instance(self):
        with ModelMocker(Manufacturer):
            with ModelMocker(Car, outer=False):
                manufacturer = Manufacturer.objects.create(name='foo')
                obj = Car.objects.create(speed=10, make=manufacturer)
                obj.make = Manufacturer.objects.create(name='bar')
                obj.save()

                self.assertEqual(Car.objects.get(pk=obj.id).make.name, 'bar')

    def test_model_mocker_with_custom_method(self):
        with self.CarModelMocker(Car, 'validate_price') as mocker:
            obj = Car()
            obj.save()

            mocker.method('validate_price').assert_called_with()

    @CarModelMocker(Car, 'validate_price')
    def test_model_mocker_callable_with_custom_method(self, mocker):
        obj = Car()
        obj.save()

        mocker.method('validate_price').assert_called_with()

    def test_model_mocker_event_added_from_manager(self):
        objects = {}

        def car_added(obj):
            objects['added'] = obj

        with ModelMocker(Car) as mocker:
            mocker.objects.on('added', car_added)
            objects['car'] = Car.objects.create(speed=300)

        self.assertIsInstance(objects['added'], Car)
        self.assertEqual(objects['added'], objects['car'])

    def test_model_mocker_event_added_from_instance(self):
        objects = {}

        def car_added(obj):
            objects['added'] = obj

        with ModelMocker(Car) as mocker:
            mocker.objects.on('added', car_added)
            objects['car'] = Car(speed=300)
            objects['car'].save()

        self.assertIsInstance(objects['added'], Car)
        self.assertEqual(objects['added'], objects['car'])

    def test_model_mocker_delete_from_instance_with_nested_context_manager(self):

        def create_delete_models():
            car = Car.objects.create(speed=10)
            car.delete()

            manufacturer = Manufacturer.objects.create(name='foo')
            manufacturer.delete()

        def models_exist():
            return Manufacturer.objects.exists() or Car.objects.exists()

        with ModelMocker(Manufacturer), ModelMocker(Car):
            create_delete_models()
            assert not models_exist()

        # Test same scenario with reversed context manager order
        with ModelMocker(Car), ModelMocker(Manufacturer):
            create_delete_models()
            assert not models_exist()

    def test_model_mocker_event_updated_from_manager(self):
        objects = {}

        def car_updated(obj):
            objects['updated'] = obj

        with ModelMocker(Car) as mocker:
            mocker.objects.on('updated', car_updated)
            objects['car'] = Car.objects.create(speed=300)
            Car.objects.update(speed=400)

        self.assertIsInstance(objects['updated'], Car)
        self.assertEqual(objects['updated'], objects['car'])

    def test_model_mocker_event_updated_from_instance(self):
        objects = {}

        def car_updated(obj):
            objects['updated'] = obj

        with ModelMocker(Car) as mocker:
            mocker.objects.on('updated', car_updated)
            objects['car'] = Car.objects.create(speed=300)
            objects['car'].save()

        self.assertIsInstance(objects['updated'], Car)
        self.assertEqual(objects['updated'], objects['car'])

    def test_model_mocker_event_deleted_from_manager(self):
        objects = {}

        def car_deleted(obj):
            objects['deleted'] = obj

        with ModelMocker(Car) as mocker:
            mocker.objects.on('deleted', car_deleted)
            objects['car'] = Car.objects.create(speed=300)
            Car.objects.delete()

        self.assertIsInstance(objects['deleted'], Car)
        self.assertEqual(objects['deleted'], objects['car'])

    def test_model_mocker_event_deleted_from_instance(self):
        objects = {}

        def car_deleted(obj):
            objects['deleted'] = obj

        with ModelMocker(Car) as mocker:
            mocker.objects.on('deleted', car_deleted)
            objects['car'] = Car.objects.create(speed=300)
            objects['car'].delete()

        self.assertIsInstance(objects['deleted'], Car)
        self.assertEqual(objects['deleted'], objects['car'])

    def test_model_mocker_does_not_interfere_with_non_mocked_models(self):
        original_objects = CarVariation.objects

        with ModelMocker(Manufacturer) as make_mocker:
            self.assertEqual(Manufacturer.objects, make_mocker.objects)

            with ModelMocker(Car, outer=False) as car_mocker:
                self.assertEqual(Car.objects, car_mocker.objects)
                self.assertEqual(CarVariation.objects, original_objects)

                with self.assertRaises(NotSupportedError):
                    CarVariation.objects.create(color='blue')

                with self.assertRaises(NotSupportedError):
                    CarVariation(color='blue').save()

                with self.assertRaises(NotSupportedError):
                    CarVariation(id=1, color='blue').save()

                with self.assertRaises(NotSupportedError):
                    CarVariation(pk=1).delete()

                with self.assertRaises(NotSupportedError):
                    CarVariation.objects.all().delete()
