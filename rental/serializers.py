from django.db.models import Q
from rest_framework import serializers

from .models import Rental


class RentalSerializer(serializers.ModelSerializer):
    car_info = serializers.CharField(source="car", read_only=True)

    class Meta:
        model = Rental
        fields = ("id", "car", "car_info", "start_date", "end_date", "actual_return_date", "status")
        read_only_fields = ("id", "actual_return_date", "status")


class RentalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ("id", "car", "start_date", "end_date")

    def validate(self, attrs):
        start_date = attrs["start_date"]
        end_date = attrs["end_date"]
        car = attrs["car"]

        if start_date > end_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})

        overlapping_rentals_count = (
            Rental.objects.filter(car=car, status=Rental.Status.BOOKED)
            .filter(Q(start_date__lte=end_date) & Q(end_date__gte=start_date))
            .count()
        )

        if overlapping_rentals_count >= car.inventory:
            raise serializers.ValidationError({"car": "No cars available for selected dates."})

        return attrs

    def create(self, validated_data):
        rental = Rental.objects.create(user=self.context["request"].user, status=Rental.Status.BOOKED, **validated_data)

        # TODO: Asynchronous notification task
        # send_rental_confirmation.delay(rental.id)

        return rental
