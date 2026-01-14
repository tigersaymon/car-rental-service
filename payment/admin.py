from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("rental", "status", "type", "money_to_pay")
    list_filter = ("status", "type")
