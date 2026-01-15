from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

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
        on_delete=models.PROTECT,
        related_name="rentals",
    )

    start_date = models.DateField()
    end_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["car", "start_date", "end_date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user}: {self.car} ({self.start_date})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_("End date cannot be before start date."))

        if self.start_date and self.start_date < timezone.now().date() and not self.pk:
            raise ValidationError(_("Start date cannot be in the past."))
