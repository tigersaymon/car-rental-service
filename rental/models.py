from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from car.models import Car


class Rental(models.Model):
    class Status(models.TextChoices):
        BOOKED = "BOOKED", _("Booked")
        COMPLETED = "COMPLETED", _("Completed")
        CANCELLED = "CANCELLED", _("Cancelled")
        OVERDUE = "OVERDUE", _("Overdue")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rentals",
    )
    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="rentals",
    )

    start_date = models.DateField()
    end_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.car} ({self.start_date})"

    @property
    def price_per_day(self):
        return self.car.daily_rate
