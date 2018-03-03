from django.db import models
from rest_framework import serializers


class Manufacturer(models.Model):
    name = models.CharField(max_length=25)


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ('id', 'name',)


class Car(models.Model):
    make = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    model = models.CharField(max_length=25, blank=True, null=True)
    speed = models.IntegerField()

    def format_speed(self):
        return '{0} km/h'.format(self.speed)

    def validate_price(self):
        """ Validate price against manufacturer remote api """

    def save(self, *args, **kwargs):
        self.validate_price()
        super(Car, self).save(*args, **kwargs)


class CarVariation(models.Model):
    car = models.ForeignKey(Car, related_name='variations', on_delete=models.CASCADE)
    color = models.CharField(max_length=100)


class Sedan(Car):
    pass


class Passenger(models.Model):
    car = models.ForeignKey(Car, related_name='passengers', on_delete=models.CASCADE)
    name = models.CharField(max_length=25)


class CarSerializer(serializers.ModelSerializer):
    make = ManufacturerSerializer()
    speed = serializers.SerializerMethodField()

    def get_speed(self, obj):
        return obj.format_speed()

    class Meta:
        model = Car
        fields = ('id', 'make', 'model', 'speed',)
