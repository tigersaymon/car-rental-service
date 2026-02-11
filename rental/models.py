from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from car.models import Car


class Rental(models.Model):
    """
    Represents a rental agreement between a user and a car.
    """

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

    def __str__(self) -> str:
        return f"{self.user}: {self.car} ({self.start_date})"

    def save(self, *args, **kwargs) -> None:
        """
        Overrides the save method to perform full validation before saving.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """
        Performs custom validation for the model.

        Raises:
            ValidationError: If end_date is before start_date or start_date is in the past.
        """
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_("End date cannot be before start date."))

        if self.start_date and self.start_date < timezone.now().date() and not self.pk:
            raise ValidationError(_("Start date cannot be in the past."))

    @property
    def total_cost(self) -> Decimal:
        """
        Calculates the total cost of the rental based on duration and car's daily rate.

        Returns:
            Decimal: The total cost.
        """
        days = (self.end_date - self.start_date).days + 1
        return days * self.car.daily_rate
