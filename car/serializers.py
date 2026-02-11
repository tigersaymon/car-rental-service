from rest_framework import serializers

from .models import Car


class CarSerializer(serializers.ModelSerializer):
    """
    Base serializer for Car model.

    Provides fundamental fields including image.
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
            "image",
        )


class CarListSerializer(CarSerializer):
    """
    Serializer for listing cars.

    Includes cars_available field for quick overview.
    """

    cars_available = serializers.IntegerField(read_only=True)

    class Meta(CarSerializer.Meta):
        fields = CarSerializer.Meta.fields + ("cars_available",)


class CarDetailSerializer(CarSerializer):
    """
    Serializer for detailed car view.

    Includes fuel type and image.
    """

    class Meta(CarSerializer.Meta):
        fields = CarSerializer.Meta.fields


class CarImageSerializer(serializers.ModelSerializer):
    """
    Serializer dedicated to uploading car images.

    Used in custom upload_image action in CarViewSet.
    """

    class Meta:
        model = Car
        fields = ("id", "image")
