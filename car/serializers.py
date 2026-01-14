from rest_framework import serializers
from .models import Car


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = [
            "id",
            "brand",
            "model",
            "year",
            "fuel_type",
            "daily_rate",
            "inventory",
        ]

    def validate_inventory(self, value): # noqa
        if value < 0:
            raise serializers.ValidationError("Inventory cannot be negative")
        return value

    def validate_daily_rate(self, value): # noqa
        if value <= 0:
            raise serializers.ValidationError("Daily rate must be positive")
        return value
