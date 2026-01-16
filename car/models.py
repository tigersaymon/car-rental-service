import os
import uuid

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def car_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.brand)}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads/cars/", filename)


class Car(models.Model):
    class FuelType(models.TextChoices):
        GAS = "GAS", _("Gas")
        DIESEL = "DIESEL", _("Diesel")
        HYBRID = "HYBRID", _("Hybrid")
        ELECTRIC = "ELECTRIC", _("Electric")

    brand = models.CharField(max_length=63)
    model = models.CharField(max_length=63)
    year = models.IntegerField()
    fuel_type = models.CharField(max_length=10, choices=FuelType.choices)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.PositiveIntegerField()
    image = models.ImageField(null=True, upload_to=car_image_file_path)

    class Meta:
        ordering = ["brand", "model"]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
