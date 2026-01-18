from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from car.models import Car
from payment.models import Payment
from rental.models import Rental
from rental.serializers import (
    RentalCreateSerializer,
    RentalDetailSerializer,
    RentalListSerializer,
    RentalReturnSerializer,
)


class RentalSerializerTest(TestCase):
    """
    Test suite for Rental serializers including validation logic.
    """

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email="test@example.com",
            password="testpassword123",
        )
        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type="Petrol",
            daily_rate=Decimal("100.00"),
            inventory=2,
        )
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.user = self.user

        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)

    def test_rental_list_serializer(self) -> None:
        """
        Test that RentalListSerializer contains expected fields and nested car data.
        """
        rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        serializer = RentalListSerializer(rental)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "car", "start_date", "end_date", "status", "total_cost"})
        self.assertEqual(data["car"]["brand"], self.car.brand)
        self.assertEqual(data["car"]["model"], self.car.model)

    def test_rental_detail_serializer(self) -> None:
        """
        Test that RentalDetailSerializer includes detailed fields.
        """
        rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        serializer = RentalDetailSerializer(rental)
        data = serializer.data

        self.assertIn("user", data)
        self.assertIn("actual_return_date", data)
        self.assertIn("created_at", data)
        self.assertEqual(data["user"], self.user.id)

    def test_create_serializer_valid_data(self) -> None:
        """
        Test that RentalCreateSerializer validates correct data successfully.
        """
        data = {
            "car": self.car.id,
            "start_date": self.today,
            "end_date": self.tomorrow,
        }
        serializer = RentalCreateSerializer(data=data, context={"request": self.request})
        self.assertTrue(serializer.is_valid())
        rental = serializer.save()

        self.assertEqual(rental.user, self.user)
        self.assertEqual(rental.status, Rental.Status.BOOKED)

    def test_create_serializer_fails_with_pending_payment(self) -> None:
        """
        Test that validation fails if the user has a PENDING payment.
        """
        past_rental = Rental(
            user=self.user,
            car=self.car,
            start_date=self.today - timedelta(days=5),
            end_date=self.today - timedelta(days=4),
            status=Rental.Status.COMPLETED,
        )
        Rental.objects.bulk_create([past_rental])
        past_rental = Rental.objects.get(user=self.user,
                                         status=Rental.Status.COMPLETED)

        Payment.objects.create(
            rental=past_rental,
            status=Payment.Status.PENDING,
            type=Payment.Type.RENTAL,
            money_to_pay=Decimal("100.00"),
            session_url="http://test.com",
            session_id="sess_123",
        )

        data = {
            "car": self.car.id,
            "start_date": self.today,
            "end_date": self.tomorrow,
        }
        serializer = RentalCreateSerializer(data=data,
                                            context={"request": self.request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("You have pending payments", str(serializer.errors))

    def test_create_serializer_fails_with_active_rental_limit(self) -> None:
        """
        Test that validation fails if the user already has 3 active rentals.
        """
        for _ in range(3):
            Rental.objects.create(
                user=self.user,
                car=self.car,
                start_date=self.today,
                end_date=self.tomorrow,
                status=Rental.Status.BOOKED,
            )

        data = {
            "car": self.car.id,
            "start_date": self.today,
            "end_date": self.tomorrow,
        }
        serializer = RentalCreateSerializer(data=data, context={"request": self.request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("You cannot rent more than 3 cars", str(serializer.errors))

    def test_create_serializer_fails_invalid_dates(self) -> None:
        """
        Test that validation fails if end_date is before start_date.
        """
        data = {
            "car": self.car.id,
            "start_date": self.tomorrow,
            "end_date": self.today,
        }
        serializer = RentalCreateSerializer(data=data, context={"request": self.request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("end_date", serializer.errors)

    def test_create_serializer_fails_no_inventory(self) -> None:
        """
        Test that validation fails if there are no available cars for the selected dates.
        """
        self.car.inventory = 1
        self.car.save()

        Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

        another_user = get_user_model().objects.create_user(email="other@test.com", password="password")
        self.request.user = another_user

        data = {
            "car": self.car.id,
            "start_date": self.today,
            "end_date": self.tomorrow,
        }
        serializer = RentalCreateSerializer(data=data, context={"request": self.request})

        self.assertFalse(serializer.is_valid())
        self.assertIn("No cars available", str(serializer.errors["car"]))

    def test_create_serializer_allows_booking_if_dates_do_not_overlap(self) -> None:
        """
        Test that validation succeeds if inventory is low but dates do not overlap.
        """
        self.car.inventory = 1
        self.car.save()

        Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

        future_start = self.today + timedelta(days=5)
        future_end = self.today + timedelta(days=6)

        data = {
            "car": self.car.id,
            "start_date": future_start,
            "end_date": future_end,
        }
        serializer = RentalCreateSerializer(data=data, context={"request": self.request})

        self.assertTrue(serializer.is_valid())

    def test_return_serializer(self) -> None:
        """
        Test that RentalReturnSerializer accepts empty data.
        """
        serializer = RentalReturnSerializer(data={})
        self.assertTrue(serializer.is_valid())
