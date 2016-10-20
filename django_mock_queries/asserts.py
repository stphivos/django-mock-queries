from mock import patch, Mock
from model_mommy import mommy

from .constants import *

SkipField = locate('rest_framework.fields.SkipField')


class SerializerAssert:
    _obj = None
    _serializer = None
    _return_fields = []
    _mock_fields = []
    _expected_values = {}

    def __init__(self, cls):
        self._cls = cls

    def _get_obj(self):
        obj = self._obj or mommy.prepare(self._cls.Meta.model, _fill_optional=True)
        return obj

    def _get_attr(self, serializer, field):
        if field.field_name in self._expected_values:
            return self._expected_values[field.field_name]
        try:
            attribute = field.get_attribute(serializer.instance)

            if attribute is not None:
                attribute = field.to_representation(attribute)

            return attribute
        except SkipField:
            return SkipField

    def _get_values_patchers(self, serializer):
        values = {}
        patchers = []

        for field in serializer._readable_fields:
            if field.field_name not in self._mock_fields:
                values[field.field_name] = self._get_attr(serializer, field)
                continue

            value = None
            values[field.field_name] = value

            patchers.append(patch.object(type(field), 'to_representation', Mock(return_value=value)))

        return values, patchers

    def _test_expected_fields(self, data, values):
        for field in self._return_fields:
            if field in values and values[field] == SkipField:
                continue

            assert field in data, \
                'Field {0} missing from serializer {1}.'.format(field, self._cls)

            assert data[field] == values[field], \
                'Field {0} equals {1}, expected {2}.'.format(field, data[field], values[field])

    def _validate_args(self):
        for field in self._mock_fields:
            if field in self._expected_values:
                raise AttributeError('Cannot specify expected value for a mocked field ({0}.{1}).'
                                     .format(self._cls.Meta.model, field))

    @property
    def serializer(self):
        if not self._serializer:
            obj = self._get_obj()
            self._serializer = self._cls(obj)
        return self._serializer

    def instance(self, obj):
        self._obj = obj
        return self

    def returns(self, *fields):
        self._return_fields = fields
        return self

    def mocks(self, *fields):
        self._mock_fields = fields
        return self

    def values(self, **attrs):
        self._expected_values = attrs
        return self

    def run(self):
        self._validate_args()

        values, patchers = self._get_values_patchers(self.serializer)

        try:
            for patcher in patchers:
                patcher.start()

            self._test_expected_fields(self.serializer.data, values)
        finally:
            for patcher in patchers:
                patcher.stop()


def assert_serializer(cls):
    return SerializerAssert(cls)
