from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Payment model.
    Displays payment details including rental reference, amount, and status.
    """

    list_display = ("rental", "status", "type", "money_to_pay")
    list_filter = ("status", "type")
