from django.contrib import admin

from .models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "year", "daily_rate", "inventory")
    list_filter = ("brand", "fuel_type")
