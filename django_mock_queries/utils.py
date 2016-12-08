from mock import MagicMock
import os
import sys

import django
from django.apps import apps
from django.core.exceptions import FieldError
from django.db import connections
from django.db.backends.base import creation
from django.db.utils import ConnectionHandler, NotSupportedError

from .constants import *


def monkey_patch_test_db(disabled_features=None):
    """ Replace the real database connection with a mock one.

    Any database queries will raise a clear error, and the test database
    creation and tear down are skipped.
    Tests that require the real database should be decorated with
    @skipIfDBFeature('is_mocked')
    :param disabled_features: a list of strings that should be marked as
        *False* on the connection features list. All others will default
        to True.
    """

    def create_mock_test_db(self, *args, **kwargs):
        mock_django_connection(disabled_features)

    def destroy_mock_test_db(self, *args, **kwargs):
        pass

    creation.BaseDatabaseCreation.create_test_db = create_mock_test_db
    creation.BaseDatabaseCreation.destroy_test_db = destroy_mock_test_db


def mock_django_setup(settings_module, disabled_features=None):
    """ Must be called *AT IMPORT TIME* to pretend that Django is set up.

    This must be called before any Django models are imported, or they will
    complain. Call this from a module in the calling project at import time,
    then be sure to import that module at the start of all mock test modules.
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


def merge(first, second):
    return first + list(set(second) - set(first))


def intersect(first, second):
    return list(set(first).intersection(second))


# noinspection PyProtectedMember
def find_field_names(obj):
    field_names = set()
    field_names.update(obj._meta._forward_fields_map.keys())
    field_names.update(obj._meta.fields_map.keys())
    for parent in obj._meta.parents.keys():
        parent_fields = find_field_names(parent) or []
        field_names.update(parent_fields)
    return sorted(field_names)


def get_attribute(obj, attr, default=None):
    result = obj
    comparison = None
    parts = attr.split('__')

    for p in parts:
        if p in COMPARISONS:
            comparison = p
        elif result is None:
            break
        else:
            field_names = find_field_names(result)
            if p != 'pk' and field_names and p not in field_names:
                message = "Cannot resolve keyword '{}' into field. Choices are {}.".format(
                    p,
                    ', '.join(map(repr, map(str, field_names)))
                )
                raise FieldError(message)
            result = getattr(result, p, None)

    value = result if result is not None else default
    return value, comparison


def is_match(first, second, comparison=None):
    if not comparison:
        return first == second
    return {
        COMPARISON_EXACT: lambda: first == second,
        COMPARISON_IEXACT: lambda: first.lower() == second.lower(),
        COMPARISON_CONTAINS: lambda: second in first,
        COMPARISON_ICONTAINS: lambda: second.lower() in first.lower(),
        COMPARISON_GT: lambda: first > second,
        COMPARISON_GTE: lambda: first >= second,
        COMPARISON_LT: lambda: first < second,
        COMPARISON_LTE: lambda: first <= second,
        COMPARISON_IN: lambda: first in second,
        COMPARISON_ISNULL: lambda: (first is None) == bool(second),
    }[comparison]()


def matches(*source, **attrs):
    exclude = []
    for x in source:
        for attr_name, filter_value in attrs.items():
            attr_value, comparison = get_attribute(x, attr_name)
            if not is_match(attr_value, filter_value, comparison):
                exclude.append(x)
                break
    for x in source:
        if x not in exclude:
            yield x
