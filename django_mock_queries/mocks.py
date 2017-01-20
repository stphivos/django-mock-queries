import os
import sys
import django

from django.apps import apps
from django.db import connections
from django.db.backends.base import creation
from django.db.utils import ConnectionHandler, NotSupportedError
from mock import MagicMock, patch, PropertyMock

from .query import MockSet


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
    def compiler(queryset, connection, using, **kwargs):
        result = MagicMock(name='mock_connection.ops.compiler()')
        # noinspection PyProtectedMember
        result.execute_sql.side_effect = NotSupportedError(
            "Mock database tried to execute SQL for {} model.".format(
                queryset.model._meta.object_name))
        return result

    mock_ops.compiler.return_value.side_effect = compiler
    mock_ops.integer_field_range.return_value = (-sys.maxsize - 1, sys.maxsize)
    mock_ops.max_name_length.return_value = sys.maxsize


class Mocker(object):
    """
    A decorator that patches multiple class methods with a magic mock instance that does nothing.
    """

    def __init__(self, cls, *methods):
        self.cls = cls
        self.methods = methods

    def __enter__(self):
        self.mocks = {}
        self.patchers = {}

        for method in self.methods:
            replacement_method = '_'.join(method.split('.'))
            target_cls, target_method = self.get_target_method(self.cls, method)
            mock_cls = MagicMock if callable(getattr(target_cls, target_method)) else PropertyMock

            patcher = patch.object(target_cls, target_method, mock_cls(
                name='{}.{}'.format(target_cls, method),
                side_effect=getattr(self, replacement_method, MagicMock())
            ))

            self.patchers[method] = patcher
            self.mocks[method] = patcher.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self.patchers.values():
            patcher.stop()

    def method(self, name):
        return self.mocks[name]

    def get_target_method(self, cls, method):
        target_obj = cls
        parts = method.split('.')

        target_method = parts[-1]
        parts = parts[:-1]

        while parts:
            target_obj = getattr(target_obj, parts[0], None) or getattr(target_obj.model, '_' + parts[0])
            parts.pop(0)

        return target_obj, target_method


class ModelMocker(Mocker):
    """
    A decorator that patches django base model's db read/write methods and wires them to a MockSet.
    """

    qs = MockSet()
    default_methods = ('objects', '_meta.base_manager._insert', '_do_update')

    def __init__(self, cls, *methods):
        super(ModelMocker, self).__init__(cls, *(self.default_methods + methods))

    def objects(self):
        return self.qs

    def _meta_base_manager__insert(self, objects, *args, **kwargs):
        obj = objects[0]

        obj.pk = max([x.pk for x in self.qs] + [0]) + 1
        self.qs.add(obj)

        return obj.pk

    def _do_update(self, base_qs, using, pk_val, values, *args, **kwargs):
        if not self.qs.filter(pk=pk_val).exists():
            return False

        for field, _, value in values:
            if not (value is None and not field.null):
                setattr(self.qs.get(pk=pk_val), field.name, value)

        return True
