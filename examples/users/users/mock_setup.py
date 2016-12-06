""" This module contains utilities for pure unit tests.

It must be imported from mock_test modules before any model classes, or they
will complain.
"""

from django_mock_queries.utils import mock_django_setup

mock_django_setup('users.settings')
