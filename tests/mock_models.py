from django.db import models
from rest_framework import serializers


class Manufacturer(models.Model):
    name = models.CharField(max_length=25)


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ('id', 'name',)


class Car(models.Model):
    make = models.ForeignKey(Manufacturer)
    model = models.CharField(max_length=25, blank=True, null=True)
    speed = models.IntegerField()

    def format_speed(self):
        return '{0} km/h'.format(self.speed)


class CarSerializer(serializers.ModelSerializer):
    make = ManufacturerSerializer()
    speed = serializers.SerializerMethodField()

    def get_speed(self, obj):
        return obj.format_speed()

    class Meta:
        model = Car
        fields = ('id', 'make', 'model', 'speed',)
