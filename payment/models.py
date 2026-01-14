from django.db import models
from django.utils.translation import gettext_lazy as _

from rental.models import Rental


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PAID = "PAID", _("Paid")
        EXPIRED = "EXPIRED", _("Expired")

    class Type(models.TextChoices):
        RENTAL = "RENTAL", _("Rental")
        CANCELLATION_FEE = "CANCELLATION_FEE", _("Cancellation Fee")
        OVERDUE_FEE = "OVERDUE_FEE", _("Overdue Fee")

    rental = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    type = models.CharField(max_length=20, choices=Type.choices)

    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} ({self.status})"
