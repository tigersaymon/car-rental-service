from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from car.models import Car
from rental.models import Rental


class RentalModelTest(TestCase):
    """
    Test suite for the Rental model logic, validations, and properties.
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
            inventory=5,
        )
        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)

    def test_rental_string_representation(self) -> None:
        """
        Test the string representation of the Rental model.
        """
        rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        expected_str = f"{self.user}: {self.car} ({self.today})"
        self.assertEqual(str(rental), expected_str)

    def test_rental_total_cost_calculation(self) -> None:
        """
        Test that the total_cost property calculates correctly based on duration and daily_rate.
        """
        rental = Rental(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        expected_cost = Decimal("200.00")
        self.assertEqual(rental.total_cost, expected_cost)

        rental_single_day = Rental(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.today,
        )
        expected_cost_single = Decimal("100.00")
        self.assertEqual(rental_single_day.total_cost, expected_cost_single)

    def test_validation_error_if_end_date_before_start_date(self) -> None:
        """
        Test that creating a rental with end_date before start_date raises ValidationError.
        """
        rental = Rental(
            user=self.user,
            car=self.car,
            start_date=self.tomorrow,
            end_date=self.today,
        )
        with self.assertRaises(ValidationError):
            rental.save()

    def test_validation_error_if_start_date_in_past(self) -> None:
        """
        Test that creating a new rental with a start_date in the past raises ValidationError.
        """
        yesterday = self.today - timedelta(days=1)
        rental = Rental(
            user=self.user,
            car=self.car,
            start_date=yesterday,
            end_date=self.today,
        )
        with self.assertRaises(ValidationError):
            rental.save()

    def test_allow_past_start_date_on_update(self) -> None:
        """
        Test that updating an existing rental does not trigger the 'start date in past' validation.
        This ensures historic rentals can be modified (e.g., status changed).
        """
        rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )

        rental.start_date = self.today - timedelta(days=5)
        rental.end_date = self.today - timedelta(days=4)

        try:
            rental.save()
        except ValidationError:
            self.fail("ValidationError raised on updating existing rental with past date")

    def test_default_status_is_booked(self) -> None:
        """
        Test that a new rental receives the default status 'BOOKED'.
        """
        rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        self.assertEqual(rental.status, Rental.Status.BOOKED)
