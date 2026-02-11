from django.contrib import admin

from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    """
    Admin configuration for Car model.

    Displays brand, model, year, daily rate, and inventory in list view.
    Allows filtering by brand and fuel type.
    """

    list_display = ("brand", "model", "year", "daily_rate", "inventory")
    list_filter = ("brand", "fuel_type")
