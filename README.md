[![Latest Version](https://img.shields.io/pypi/v/django_mock_queries.svg)](https://pypi.python.org/pypi/django_mock_queries)
[![Build Status](https://travis-ci.org/stphivos/django-mock-queries.svg?branch=master)](https://travis-ci.org/stphivos/django-mock-queries)
[![Code Coverage](https://codecov.io/github/stphivos/django-mock-queries/coverage.svg?branch=master)](https://codecov.io/github/stphivos/django-mock-queries?branch=master)
[![Code Climate](https://codeclimate.com/github/stphivos/django-mock-queries/badges/gpa.svg)](https://codeclimate.com/github/stphivos/django-mock-queries)

# Django Mock Queries

A library for mocking django queryset functions in memory for testing

## Features

* QuerySet style support for method chaining
* Filtering with Q objects
* Aggregates generation
* CRUD functions
* Field lookups
* django-rest-framework serializer asserts

## Examples

```python
from django.db.models import Avg, Q
from django_mock_queries.query import MockSet, MockModel

qs = MockSet(
    MockModel(mock_name='john', email='john@gmail.com'),
    MockModel(mock_name='jeff', email='jeff@hotmail.com'),
    MockModel(mock_name='bill', email='bill@gmail.com'),
)

print [x for x in qs.all().filter(email__icontains='gmail.com').select_related('address')]
# Outputs: [john, bill]

qs = MockSet(
    MockModel(mock_name='model s', msrp=70000),
    MockModel(mock_name='model x', msrp=80000),
    MockModel(mock_name='model 3', msrp=35000),
)

print qs.all().aggregate(Avg('msrp'))
# Outputs: {'msrp__avg': 61666}

qs = MockSet(
    MockModel(mock_name='model x', make='tesla', country='usa'),
    MockModel(mock_name='s-class', make='mercedes', country='germany'),
    MockModel(mock_name='s90', make='volvo', country='sweden'),
)

print [x for x in qs.all().filter(Q(make__iexact='tesla') | Q(country__iexact='germany'))]
# Outputs: [model x, s-class]

qs = MockSet(cls=MockModel)
print qs.create(mock_name='my_object', foo='1', bar='a')
# Outputs: my_object

print [x for x in qs]
# Outputs: [my_object]
```

Writing a test for a function that uses QuerySet method filter:

```python
"""
Function that queries active users
"""
def active_users(self):
    return User.objects.filter(is_active=True).all()

"""
Test function applies expected filters by patching django's user model Manager or Queryset with a MockSet
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

Writing a test for a django-rest-framework serializer:

```python
"""
Car model serializer that includes a nested serializer and a method field
"""
class CarSerializer(serializers.ModelSerializer):
    make = ManufacturerSerializer()
    speed = serializers.SerializerMethodField()

    def get_speed(self, obj):
        return obj.format_speed()

    class Meta:
        model = Car
        fields = ('id', 'make', 'model', 'speed',)

"""
Test serializer returns expected fields with specified values and mock the result of nested serializer for field make
"""
def test_car_serializer_fields(self):
    car = Car(id=1, make=Manufacturer(id=1, name='vw'), model='golf', speed=300)

    values = {
        'id': car.id,
        'model': car.model,
        'speed': car.formatted_speed(),
    }

    assert_serializer(CarSerializer) \
        .instance(car) \
        .returns('id', 'make', 'model', 'speed') \
        .values(**values) \
        .mocks('make') \
        .run()
```

## Installation

```bash
$ pip install django_mock_queries
```

## Contributing

Anything missing or not functioning correctly? PRs are always welcome! Otherwise, you can create an issue so someone else does it when time allows.

You can follow these guidelines:

* Fork the repo from this page
* Clone your fork:
```bash
$ git clone https://github.com/{your-username}/django-mock-queries.git
$ cd django-mock-queries
$ git checkout -b feature/your_cool_feature
```
* Implement feature/fix
* Add/modify relevant tests
* Run tox to verify all tests and flake8 quality checks pass
```bash
$ tox
```
* Commit and push local branch to your origin
```bash
$ git commit . -m "New cool feature does this"
$ git push -u origin HEAD
```
* Create pull request

## TODO

* Add custom asserts for django-rest-framework serializers/views
* Add support for missing queryset functions and field lookups
* Implement decorators for unified model patching
