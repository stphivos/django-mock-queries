import os
import sys
import django
import weakref
from django.apps import apps
from django.db import connections
from django.db.backends.base import creation
from django.db.models import Model
from django.db.utils import ConnectionHandler, NotSupportedError
from functools import partial
from itertools import chain
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from types import MethodType

from .query import MockSet

# noinspection PyUnresolvedReferences
patch_object = patch.object


def monkey_patch_test_db(disabled_features=None):
    """ Replace the real database connection with a mock one.

    This is useful for running Django tests without the cost of setting up a
    test database.
    Any database queries will raise a clear error, and the test database
    creation and tear down are skipped.
    Tests that require the real database should be decorated with
    @skipIfDBFeature('is_mocked')
    :param disabled_features: a list of strings that should be marked as
        *False* on the connection features list. All others will default
        to True.
    """

    # noinspection PyUnusedLocal
    def create_mock_test_db(self, *args, **kwargs):
        mock_django_connection(disabled_features)

    # noinspection PyUnusedLocal
    def destroy_mock_test_db(self, *args, **kwargs):
        pass

    creation.BaseDatabaseCreation.create_test_db = create_mock_test_db
    creation.BaseDatabaseCreation.destroy_test_db = destroy_mock_test_db


def mock_django_setup(settings_module, disabled_features=None):
    """ Must be called *AT IMPORT TIME* to pretend that Django is set up.

    This is useful for running tests without using the Django test runner.
    This must be called before any Django models are imported, or they will
    complain. Call this from a module in the calling project at import time,
    then be sure to import that module at the start of all mock test modules.
    Another option is to call it from the test package's init file, so it runs
    before all the test modules are imported.
    :param settings_module: the module name of the Django settings file,
        like 'myapp.settings'
    :param disabled_features: a list of strings that should be marked as
        *False* on the connection features list. All others will default
        to True.
    """
    if apps.ready:
        # We're running in a real Django unit test, don't do anything.
        return

    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
    django.setup()
    mock_django_connection(disabled_features)


def mock_django_connection(disabled_features=None):
    """ Overwrite the Django database configuration with a mocked version.

    This is a helper function that does the actual monkey patching.
    """
    db = connections.databases['default']
    db['PASSWORD'] = '****'
    db['USER'] = '**Database disabled for unit tests**'
    ConnectionHandler.__getitem__ = MagicMock(name='mock_connection')
    # noinspection PyUnresolvedReferences
    mock_connection = ConnectionHandler.__getitem__.return_value
    if disabled_features:
        for feature in disabled_features:
            setattr(mock_connection.features, feature, False)
    mock_ops = mock_connection.ops

    # noinspection PyUnusedLocal
    def compiler(queryset, using=None, connection=None, elide_empty=True, **kwargs):
        result = MagicMock(name='mock_connection.ops.compiler()')
        # noinspection PyProtectedMember
        result.execute_sql.side_effect = NotSupportedError(
            "Mock database tried to execute SQL for {} model.".format(
                queryset.model._meta.object_name))
        result.has_results.side_effect = result.execute_sql.side_effect
        return result

    mock_ops.compiler.return_value.side_effect = compiler
    mock_ops.integer_field_range.return_value = (-sys.maxsize - 1, sys.maxsize)
    mock_ops.max_name_length.return_value = sys.maxsize

    Model.refresh_from_db = Mock()  # Make this into a noop.


class MockMap:
    def __init__(self, original):
        """ Wrap a mock mapping around the original one-to-many relation. """
        self.map = {}
        self.original = original

    def __set__(self, instance, value):
        """ Set a related object for an instance. """

        self.map[id(instance)] = (weakref.ref(instance), value)

    def __getattr__(self, name):
        """ Delegate all other calls to the original. """

        return getattr(self.original, name)


class MockOneToManyMap(MockMap):
    def __get__(self, instance, owner):
        """ Look in the map to see if there is a related set.

        If not, create a new set.
        """

        if instance is None:
            # Call was to the class, not an object.
            return self

        instance_id = id(instance)
        entry = self.map.get(instance_id)
        old_instance = related_objects = None
        if entry is not None:
            old_instance_weak, related_objects = entry
            old_instance = old_instance_weak()
        if entry is None or old_instance is None:
            related = getattr(self.original, 'related', self.original)
            related_objects = MockSet(model=related.field.model)
            self.__set__(instance, related_objects)

        return related_objects


class MockOneToOneMap(MockMap):
    def __get__(self, instance, owner):
        """ Look in the map to see if there is a related object.

        If not (the default) raise the expected exception.
        """

        if instance is None:
            # Call was to the class, not an object.
            return self

        entry = self.map.get(id(instance))
        old_instance = related_object = None
        if entry is not None:
            old_instance_weak, related_object = entry
            old_instance = old_instance_weak()
        if entry is None or old_instance is None:
            raise self.original.RelatedObjectDoesNotExist(
                "Mock %s has no %s." % (
                    owner.__name__,
                    self.original.related.get_accessor_name()
                )
            )
        return related_object


def find_all_models(models):
    """ Yield all models and their parents. """
    for model in models:
        yield model
        # noinspection PyProtectedMember
        for parent in model._meta.parents.keys():
            for parent_model in find_all_models((parent,)):
                yield parent_model


def _patch_save(model, name):
    return patch_object(
        model,
        'save',
        new_callable=partial(Mock, name=name + '.save')
    )


def _patch_objects(model, name):
    return patch_object(
        model, 'objects',
        new_callable=partial(MockSet, mock_name=name + '.objects', model=model)
    )


def _patch_relation(model, name, related_object):
    relation = getattr(model, name)

    if related_object.one_to_one:
        new_callable = partial(MockOneToOneMap, relation)
    else:
        new_callable = partial(MockOneToManyMap, relation)

    return patch_object(model, name, new_callable=new_callable)


# noinspection PyProtectedMember
def mocked_relations(*models):
    """ Mock all related field managers to make pure unit tests possible.

    The resulting patcher can be used just like one from the mock module:
    As a test method decorator, a test class decorator, a context manager,
    or by just calling start() and stop().

    @mocked_relations(Dataset):
    def test_dataset(self):
        dataset = Dataset()
        check = dataset.content_checks.create()  # returns a ContentCheck object
    """
    patchers = []

    for model in find_all_models(models):
        if isinstance(model.save, Mock):
            # already mocked, so skip it
            continue

        model_name = model._meta.object_name
        patchers.append(_patch_save(model, model_name))

        if hasattr(model, 'objects'):
            patchers.append(_patch_objects(model, model_name))

        for related_object in chain(model._meta.related_objects,
                                    model._meta.many_to_many):
            name = related_object.name

            if name not in model.__dict__ and related_object.one_to_many:
                name += '_set'

            if name in model.__dict__:
                # Only mock direct relations, not inherited ones.
                if getattr(model, name, None):
                    patchers.append(_patch_relation(
                        model, name, related_object
                    ))

    return PatcherChain(patchers, pass_mocks=False)


class PatcherChain:
    """ Chain a list of mock patchers into one.

    The resulting patcher can be used just like one from the mock module:
    As a test method decorator, a test class decorator, a context manager,
    or by just calling start() and stop().
    """

    def __init__(self, patchers, pass_mocks=True):
        """ Initialize a patcher.

        :param patchers: a list of patchers that should all be applied
        :param pass_mocks: True if any mock objects created by the patchers
        should be passed to any decorated test methods.
        """
        self.patchers = patchers
        self.pass_mocks = pass_mocks

    def __call__(self, func):
        if isinstance(func, type):
            decorated = self.decorate_class(func)
        else:
            decorated = self.decorate_callable(func)
        # keep the previous class/function name
        decorated.__name__ = func.__name__

        return decorated

    def decorate_class(self, cls):
        for attr in dir(cls):
            # noinspection PyUnresolvedReferences
            if not attr.startswith(patch.TEST_PREFIX):
                continue

            attr_value = getattr(cls, attr)
            if not hasattr(attr_value, "__call__"):
                continue

            setattr(cls, attr, self(attr_value))
        return cls

    def decorate_callable(self, target):
        """ Called as a decorator. """

        # noinspection PyUnusedLocal
        def absorb_mocks(test_case, *args):
            return target(test_case)

        should_absorb = not (self.pass_mocks or isinstance(target, type))
        result = absorb_mocks if should_absorb else target
        for patcher in self.patchers:
            result = patcher(result)
        return result

    def __enter__(self):
        """ Starting a context manager.

        All the patched objects are passed as a list to the with statement.
        """
        return [patcher.__enter__() for patcher in self.patchers]

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Ending a context manager. """
        for patcher in self.patchers:
            patcher.__exit__(exc_type, exc_val, exc_tb)

    def start(self):
        return [patcher.start() for patcher in self.patchers]

    def stop(self):
        for patcher in reversed(self.patchers):
            patcher.stop()


class Mocker:
    """
    A decorator that patches multiple class methods with a magic mock instance that does nothing.
    """

    def __init__(self, cls, *methods, **kwargs):
        self.cls = cls
        self.methods = methods

        self.inst_mocks = {}
        self.inst_patchers = {}
        self.inst_original = {}

    def __enter__(self):
        self._patch_object_methods(self.cls, *self.methods)
        return self

    def __call__(self, func):
        def decorated(*args, **kwargs):
            with self:
                return func(*((args[0], self) + args[1:]), **kwargs)

        # keep the previous method name
        decorated.__name__ = func.__name__

        return decorated

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self.inst_patchers.values():
            patcher.stop()

    def _key(self, method, obj=None):
        return '{}.{}'.format(obj or self.cls, method)

    def _method_obj(self, name, obj, *sources):
        d = {}
        [d.update(s) for s in sources]
        return d[self._key(name, obj=obj)]

    def method(self, name, obj=None):
        return self._method_obj(name, obj, self.inst_mocks)

    def original_method(self, name, obj=None):
        return self._method_obj(name, obj, self.inst_original)

    def _get_source_method(self, obj, method):
        source_obj = obj
        parts = method.split('.')

        source_method = parts[-1]
        parts = parts[:-1]

        while parts:
            source_obj = getattr(source_obj, parts[0], None) or getattr(source_obj.model, '_' + parts[0])
            parts.pop(0)

        return source_obj, source_method

    def _patch_method(self, method_name, source_obj, source_method):
        target_name = '_'.join(method_name.split('.'))
        target_obj = getattr(self, target_name, None)

        if target_obj is None:
            mock_args = dict(new=MagicMock())
        elif type(target_obj) == MethodType:
            mock_args = dict(new=MagicMock(autospec=True, side_effect=target_obj))
        else:
            mock_args = dict(new=PropertyMock(return_value=target_obj))

        return patch_object(source_obj, source_method, **mock_args)

    def _patch_object_methods(self, obj, *methods, **kwargs):
        original, patchers, mocks = self.inst_original, self.inst_patchers, self.inst_mocks

        for method in methods:
            key = self._key(method, obj=obj)

            source_obj, source_method = self._get_source_method(obj, method)

            if key not in original:
                original[key] = getattr(source_obj, source_method)

            if key not in patchers:
                patcher = self._patch_method(method, source_obj, source_method)
                patchers[key] = patcher
                mocks[key] = patcher.start()


class ModelMocker(Mocker):
    """
    A decorator that patches django base model's db read/write methods and wires them to a MockSet.
    """

    default_methods = ['objects', '_do_update', 'delete']

    if django.VERSION[0] >= 3:
        default_methods += ['_base_manager._insert', ]
    else:
        default_methods += ['_meta.base_manager._insert', ]

    default_methods = tuple(default_methods)

    def __init__(self, cls, *methods, **kwargs):
        super(ModelMocker, self).__init__(cls, *(self.default_methods + methods), **kwargs)

        self.objects = MockSet(model=self.cls)
        self.objects.on('added', self._on_added)

    def __enter__(self):
        result = super(ModelMocker, self).__enter__()
        return result

    def _obj_pk(self, obj):
        return getattr(obj, self.cls._meta.pk.attname, None)

    def _on_added(self, obj):
        pk = max([self._obj_pk(x) or 0 for x in self.objects] + [0]) + 1
        setattr(obj, self.cls._meta.pk.attname, pk)

    def _meta_base_manager__insert(self, objects, *_, **__):
        obj = objects[0]
        self.objects.add(obj)

        return self._obj_pk(obj)

    def _base_manager__insert(self, objects, *_, **__):
        obj = objects[0]
        self.objects.add(obj)

        # Do not set anything on the model instance itself, as we do not get any values from the database.
        # The object ID is being set automatically.
        # Reference: `django.db.models.base.Model._save_table`
        return []

    def _do_update(self, *args, **_):
        _, _, pk_val, values, _, _ = args
        objects = self.objects.filter(pk=pk_val)

        if objects.exists():
            attrs = {field.attname: value for field, _, value in values if value is not None}
            self.objects.update(**attrs)
            return True
        else:
            return False

    def delete(self, *_args, **_kwargs):
        pk = self._obj_pk(self.objects[0])
        if not pk:
            raise ValueError(
                f"{self.cls._meta.object_name} object can't be deleted because "
                f'its {self.cls._meta.pk.attname} attribute is set to None.'
            )
        return self.objects.filter(pk=pk).delete()
