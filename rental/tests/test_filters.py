from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from car.models import Car
from rental.filters import RentalFilter
from rental.models import Rental


class RentalFilterTest(TestCase):
    """
    Test suite for RentalFilter logic, specifically the dynamic visibility
    of the 'user' filter based on user permissions.
    """

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.User = get_user_model()

        self.user = self.User.objects.create_user(
            email="user@test.com",
            password="password",
        )
        self.admin = self.User.objects.create_superuser(
            email="admin@test.com",
            password="password",
        )
        self.other_user = self.User.objects.create_user(
            email="other@test.com",
            password="password",
        )

        self.car = Car.objects.create(
            brand="Test",
            model="Car",
            year=2022,
            daily_rate=Decimal("50.00"),
            inventory=5,
        )

        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)

        self.rental_booked = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )
        self.rental_completed = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
            status=Rental.Status.COMPLETED,
        )
        self.rental_other = Rental.objects.create(
            user=self.other_user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

    def test_filter_by_status(self) -> None:
        """
        Test that filtering by status works correctly for any user.
        """
        request = self.factory.get("/")
        request.user = self.user

        data = {"status": Rental.Status.COMPLETED}
        rental_filter = RentalFilter(
            data=data,
            queryset=Rental.objects.all(),
            request=request,
        )

        self.assertTrue(rental_filter.is_valid())
        self.assertEqual(rental_filter.qs.count(), 1)
        self.assertEqual(rental_filter.qs.first(), self.rental_completed)

    def test_user_filter_removed_for_non_staff(self) -> None:
        """
        Test that the 'user' filter field is removed for non-staff users.
        """
        request = self.factory.get("/")
        request.user = self.user

        rental_filter = RentalFilter(
            queryset=Rental.objects.all(),
            request=request,
        )

        self.assertNotIn("user", rental_filter.filters)

    def test_user_filter_present_for_staff(self) -> None:
        """
        Test that the 'user' filter field remains available for staff users.
        """
        request = self.factory.get("/")
        request.user = self.admin

        rental_filter = RentalFilter(
            queryset=Rental.objects.all(),
            request=request,
        )

        self.assertIn("user", rental_filter.filters)

    def test_admin_can_filter_by_user(self) -> None:
        """
        Test that an admin can successfully filter rentals by a specific user ID.
        """
        request = self.factory.get("/")
        request.user = self.admin

        data = {"user": self.other_user.id}
        rental_filter = RentalFilter(
            data=data,
            queryset=Rental.objects.all(),
            request=request,
        )

        self.assertTrue(rental_filter.is_valid())
        self.assertEqual(rental_filter.qs.count(), 1)
        self.assertEqual(rental_filter.qs.first(), self.rental_other)

    def test_user_filter_ignored_for_non_staff_if_provided(self) -> None:
        """
        Test that even if a non-staff user tries to pass a 'user' parameter,
        it is ignored because the filter field is removed.
        """
        request = self.factory.get("/")
        request.user = self.user

        data = {"user": self.other_user.id}

        rental_filter = RentalFilter(
            data=data,
            queryset=Rental.objects.all(),
            request=request,
        )

        self.assertIn(self.rental_booked, rental_filter.qs)
        self.assertNotIn("user", rental_filter.filters)
