from django.db.models import Q
from rest_framework import serializers

from car.serializers import (
    CarDetailSerializer,
    CarListSerializer,
)
from payment.models import Payment

from .models import Rental


class RentalListSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = ("id", "car", "start_date", "end_date", "status", "total_cost")


class RentalDetailSerializer(serializers.ModelSerializer):
    car = CarDetailSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = (
            "id",
            "user",
            "car",
            "start_date",
            "end_date",
            "actual_return_date",
            "status",
            "total_cost",
            "created_at",
        )


class RentalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ("id", "car", "start_date", "end_date")

    def validate(self, attrs):
        user = self.context["request"].user

        if Payment.objects.filter(rental__user=user, status=Payment.Status.PENDING).exists():
            raise serializers.ValidationError("You have pending payments! Please pay them first.")

        active_rentals_count = Rental.objects.filter(
            user=user, status__in=[Rental.Status.BOOKED, Rental.Status.OVERDUE]
        ).count()

        if active_rentals_count >= 3:
            raise serializers.ValidationError("You cannot rent more than 3 cars at the same time.")

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

        return rental


class RentalReturnSerializer(serializers.Serializer):
    pass
