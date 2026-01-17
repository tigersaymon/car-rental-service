from rest_framework import serializers

from .models import Car


class CarSerializer(serializers.ModelSerializer):
    """
    Base serializer for Car model.
    Provides fundamental fields without image or availability logic.
    """

    class Meta:
        model = Car
        fields = (
            "id",
            "brand",
            "model",
            "year",
            "fuel_type",
            "daily_rate",
            "inventory",
        )


class CarListSerializer(CarSerializer):
    """
    Serializer for listing cars.
    Includes image and cars_available field for quick overview.
    """

    cars_available = serializers.IntegerField(source="inventory", read_only=True)

    class Meta:
        model = Car
        fields = (
            "id",
            "brand",
            "model",
            "year",
            "daily_rate",
            "cars_available",
            "image",
        )


class CarDetailSerializer(CarSerializer):
    """
    Serializer for detailed car view.
    Includes fuel type, image, and cars_available field.
    """

    cars_available = serializers.IntegerField(source="inventory", read_only=True)

    class Meta:
        model = Car
        fields = (
            "id",
            "brand",
            "model",
            "year",
            "fuel_type",
            "daily_rate",
            "cars_available",
            "image",
        )


class CarImageSerializer(serializers.ModelSerializer):
    """
    Serializer dedicated to uploading car images.
    Used in custom upload_image action in CarViewSet.
    """

    class Meta:
        model = Car
        fields = ("id", "image")
