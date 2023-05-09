from unittest import TestCase, skipIf
from unittest.mock import patch

from model_bakery import baker

import django
from django_mock_queries.asserts import assert_serializer, SerializerAssert
from tests.mock_models import Car, CarSerializer, Manufacturer


class TestQuery(TestCase):
    def setUp(self):
        self.make_model = baker.prepare(Manufacturer, id=1, _fill_optional=True)
        self.car_model = baker.prepare(Car, id=1, make=self.make_model, _fill_optional=True)
        self.serializer_assert = SerializerAssert(CarSerializer)

        def set_fields(*fields):
            self.serializer_assert.serializer.Meta.fields = fields

            declared = [x for x in self.serializer_assert.serializer._declared_fields]
            for x in declared:
                if x not in fields:
                    self.serializer_assert.serializer._declared_fields.pop(x)

        self.set_serializer_fields = set_fields

    def test_assert_serializer_func_returns_assert_instance_with_cls(self):
        serializer = CarSerializer
        sa = assert_serializer(serializer)
        assert isinstance(sa, SerializerAssert)
        assert isinstance(sa._cls, type(serializer))

    def test_serializer_assert_instance_sets_obj_returns_self(self):
        result = self.serializer_assert.instance(self.car_model)
        assert result == self.serializer_assert
        assert result._obj == self.car_model

    def test_serializer_assert_returns_sets_fields_returns_self(self):
        fields = ('id', 'name')
        result = self.serializer_assert.returns(*fields)
        assert result == self.serializer_assert
        assert result._return_fields == fields

    def test_serializer_assert_mocks_sets_fields_returns_self(self):
        fields = ('id', 'name')
        result = self.serializer_assert.mocks(*fields)
        assert result == self.serializer_assert
        assert result._mock_fields == fields

    def test_serializer_assert_values_sets_attrs_returns_self(self):
        attrs = {'id': 1, 'name': 'a'}
        result = self.serializer_assert.values(**attrs)
        assert result == self.serializer_assert
        assert result._expected_values == attrs

    def test_serializer_assert_run_does_not_allow_specifying_expected_value_for_mocked_field(self):
        sa = self.serializer_assert.mocks('make').values(make=self.make_model)
        self.assertRaises(AttributeError, sa.run)

    def test_serializer_assert_run_fails_when_expected_field_missing(self):
        fields = ('id', 'model', 'speed',)
        self.set_serializer_fields(*fields)
        sa = self.serializer_assert.instance(self.car_model).returns(*(fields + ('price',)))
        self.assertRaises(AssertionError, sa.run)

    def test_serializer_assert_run_succeeds_when_expected_fields_returned(self):
        fields = ('id', 'model', 'speed',)
        self.set_serializer_fields(*fields)
        sa = self.serializer_assert.instance(self.car_model).returns(*fields)
        sa.run()

    @patch('tests.mock_models.ManufacturerSerializer.to_representation')
    def test_serializer_assert_run_does_not_call_representation_on_mocked_fields(self, to_representation_mock):
        to_representation_mock.side_effect = NotImplementedError('Error on purpose to verify mocks')
        fields = ('id', 'make', 'model', 'speed',)
        self.set_serializer_fields(*fields)
        sa = self.serializer_assert.instance(self.car_model).mocks('make').returns(*fields)
        sa.run()

    def test_serializer_assert_run_fails_when_expected_field_value_not_equal_to_specified(self):
        values = {
            'id': self.car_model.id + 1,
        }
        sa = self.serializer_assert.instance(self.car_model).returns(*values.keys()).values(**values)
        self.assertRaises(AssertionError, sa.run)

    def test_serializer_assert_run_succeeds_when_expected_field_values_all_equal_to_specified(self):
        values = {
            'id': self.car_model.id,
            'speed': self.car_model.format_speed()
        }
        sa = self.serializer_assert.instance(self.car_model).returns(*values.keys()).values(**values)
        sa.run()

    @skipIf(django.VERSION[:2] >= (1, 10),
            "Django 1.10 refreshes deleted fields from the database.")
    def test_serializer_assert_run_skips_check_for_null_field_excluded_from_serializer(self):
        delattr(self.car_model, 'model')
        sa = self.serializer_assert.instance(self.car_model).returns('model')
        sa.run()
