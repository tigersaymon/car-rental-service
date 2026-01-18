import os
import uuid

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def car_image_file_path(instance, filename):
    """
    Generate upload path for car images.

    Format:
    uploads/cars/<slug-brand>-<uuid><extension>
    """
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.brand)}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads/cars/", filename)


class Car(models.Model):
    """
    Represents a car available for rental.

    Fields:
    - brand: manufacturer name
    - model: car model name
    - year: production year
    - fuel_type: type of fuel (gas, diesel, hybrid, electric)
    - daily_rate: rental price per day
    - inventory: number of cars available
    - image: optional car image
    """

    class FuelType(models.TextChoices):
        """
        Enumeration of supported fuel types.
        """

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
        """
        Human-readable representation of the car.

        Example: "Toyota Corolla (2020)".
        """
        return f"{self.brand} {self.model} ({self.year})"
