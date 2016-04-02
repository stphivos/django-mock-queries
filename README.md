[![Latest Version](https://img.shields.io/pypi/v/django_mock_queries.svg)](https://pypi.python.org/pypi/django_mock_queries)
[![Build Status](https://travis-ci.org/stphivos/django-mock-queries.svg)](https://travis-ci.org/stphivos/django-mock-queries)
[![Code Coverage](https://codecov.io/github/stphivos/django-mock-queries/coverage.svg?branch=master)](https://codecov.io/github/stphivos/django-mock-queries?branch=master)
[![Code Climate](https://codeclimate.com/github/stphivos/django-mock-queries/badges/gpa.svg)](https://codeclimate.com/github/stphivos/django-mock-queries)

# Django Mock Queries

A django library for mocking queryset functions in memory for testing

# Examples

QuerySet style support for method chaining:

```python
from django_mock_queries.query import MockSet, MockModel

qs = MockSet(
    MockModel(mock_name='john', email='john@gmail.com'),
    MockModel(mock_name='jeff', email='jeff@hotmail.com'),
    MockModel(mock_name='bill', email='bill@gmail.com'),
)

print [x for x in qs.all().filter(email__icontains='gmail.com').select_related('address')]
# Outputs [john, bill]
```

Testing a method that uses QuerySet filter:

```python
"""
A method that queries active users
"""
def active_users(self):
    return User.objects.filter(is_active=True).all()

"""
Can be unit tested by patching django's user model Manager or Queryset with a MockSet
"""
from django_mock_queries.query import MockSet, MockModel


class TestApi(TestCase):
    users = MockSet()
    user_objects = patch('django.contrib.auth.models.User.objects', users)

    @user_objects
    def test_api_active_users_filters_by_is_active_true(self):
        self.users.add(*[
        	MockModel(mock_name='active user', is_active=True),
        	MockModel(mock_name='inactive user', is_active=False)
        ])

        for x in self.api.active_users():
        	assert x.is_active
```

# Installation

```bash
pip install django_mock_queries
```

# TODO

* Add unit test examples for: CRUD, aggregate functions, Q objects
* Implement decorators for unified model patching
* Add support for missing queryset functions and field lookups
