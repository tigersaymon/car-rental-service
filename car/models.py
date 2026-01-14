from django.db import models
from django.utils.translation import gettext_lazy as _


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

    class Meta:
        ordering = ["brand", "model"]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
