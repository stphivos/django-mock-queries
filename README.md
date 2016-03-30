[![Latest Version](https://img.shields.io/pypi/v/django_mock_queries.svg)](https://pypi.python.org/pypi/django_mock_queries)
[![Build Status](https://travis-ci.org/stphivos/django-mock-queries.svg)](https://travis-ci.org/stphivos/django-mock-queries)
[![Code Coverage](https://codecov.io/github/stphivos/django-mock-queries/coverage.svg?branch=master)](https://codecov.io/github/stphivos/django-mock-queries?branch=master)

# Django Mock Queries

A django library for mocking queryset functions in memory for testing

# Examples

A method that queries active users:
```python

def active_users(self):
    return User.objects.filter(is_active=True).all()
```

Can be unit tested by patching django's user model Manager or Queryset with a **MockSet**
```python

from django_mock_queries.query import MockSet, MockModel


class TestApi(TestCase):
    users = MockSet(cls=User)
    user_objects = patch('django.contrib.auth.models.User.objects', users)

    @user_objects
    def test_api_active_users_filters_by_is_active_true(self):
        active_user = MockModel(mock_name='active user', is_active=True)
        inactive_user = MockModel(mock_name='inactive user', is_active=False)

        self.users.add(*[active_user, inactive_user])
        results = [x for x in self.api.active_users()]

        assert active_user in results
        assert inactive_user not in results
```

# Installation

```bash
pip install django_mock_queries
```

# TODO

* Finish library tests
* Add unit test examples for: CRUD, aggregate functions, Q objects
* Implement decorators for unified model patching
