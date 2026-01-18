from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from car.models import Car
from rental.models import Rental


class RentalViewSetTestCase(APITestCase):
    """
    Base Test Case to handle common setup for all Rental tests.
    """

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testpassword123",
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpassword123",
        )

        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            daily_rate=Decimal("100.00"),
            inventory=5,
        )

        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

        self.rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

        self.list_url = reverse("rental:rental-list")
        self.detail_url = reverse("rental:rental-detail", args=[self.rental.id])
        self.return_url = reverse("rental:rental-return-car", args=[self.rental.id])
        self.cancel_url = reverse("rental:rental-cancel-rental", args=[self.rental.id])


class TestUnauthenticatedRentalAccess(RentalViewSetTestCase):
    """
    Tests for unauthenticated users. They should be blocked from everything.
    """

    def test_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_unauthorized(self):
        data = {"car": self.car.id, "start_date": self.today, "end_date": self.tomorrow}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_return_unauthorized(self):
        response = self.client.post(self.return_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAuthenticatedRentalAccess(RentalViewSetTestCase):
    """
    Tests for regular authenticated users.
    They should see their own data, but not others.
    """

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_list_rentals_shows_only_own(self):
        Rental.objects.create(
            user=self.other_user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.rental.id)

    def test_retrieve_own_rental(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.rental.id)

    def test_retrieve_others_rental_returns_404(self):
        """User cannot access another user's rental (filtered out by get_queryset)."""
        other_rental = Rental.objects.create(
            user=self.other_user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        url = reverse("rental:rental-detail", args=[other_rental.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_rental_success(self):
        data = {
            "car": self.car.id,
            "start_date": self.next_week,
            "end_date": self.next_week + timedelta(days=2),
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rental.objects.count(), 2)
        self.assertEqual(Rental.objects.last().user, self.user)

    @patch("rental.views.create_stripe_payment_for_rental")
    @patch("rental.views.notify_rental_returned.delay")
    def test_return_car_success(self, mock_notify, mock_create_payment):
        """
        Test standard return flow.
        """
        mock_payment = MagicMock()
        mock_payment.session_url = "http://stripe.com/test_session"
        mock_create_payment.return_value = mock_payment

        response = self.client.post(self.return_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rental.refresh_from_db()

        self.assertIsNotNone(self.rental.actual_return_date)
        self.assertEqual(self.rental.actual_return_date, timezone.now().date())
        self.assertNotEqual(self.rental.status, Rental.Status.COMPLETED)

        self.assertEqual(response.data["rental_payment_url"], "http://stripe.com/test_session")

    @patch("rental.views.create_stripe_payment_for_rental")
    def test_return_car_overdue(self, mock_create_payment):
        """
        Test returning a car late triggers overdue logic.
        """
        self.rental.start_date = self.today - timedelta(days=5)
        self.rental.end_date = self.today - timedelta(days=1)
        self.rental.save()

        mock_payment_rental = MagicMock()
        mock_payment_rental.session_url = "http://stripe.com/rental"
        mock_payment_fine = MagicMock()
        mock_payment_fine.session_url = "http://stripe.com/fine"

        mock_create_payment.side_effect = [mock_payment_rental, mock_payment_fine]

        response = self.client.post(self.return_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("overdue_payment_url", response.data)
        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, Rental.Status.OVERDUE)

    @patch("rental.views.notify_rental_cancelled.delay")
    def test_cancel_rental_free(self, mock_notify):
        """
        Test cancelling > 24 hours before start.
        """
        future_start = timezone.now().date() + timedelta(days=5)
        self.rental.start_date = future_start
        self.rental.end_date = future_start + timedelta(days=1)
        self.rental.save()

        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, Rental.Status.CANCELLED)

    @patch("rental.views.create_stripe_payment_for_rental")
    def test_cancel_rental_late_fee(self, mock_create_payment):
        """
        Test cancelling < 24 hours before start (today).
        """
        self.rental.start_date = timezone.now().date()
        self.rental.save()

        mock_payment = MagicMock()
        mock_payment.session_url = "http://stripe.com/cancel-fee"
        mock_create_payment.return_value = mock_payment

        response = self.client.post(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("payment_url", response.data)

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, Rental.Status.BOOKED)


class TestAdminRentalAccess(RentalViewSetTestCase):
    """
    Tests for admin users.
    """

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin)

    def test_list_all_rentals(self):
        Rental.objects.create(
            user=self.other_user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_any_rental(self):
        """Admin can retrieve other user's rental."""
        other_rental = Rental.objects.create(
            user=self.other_user,
            car=self.car,
            start_date=self.today,
            end_date=self.tomorrow,
        )
        url = reverse("rental:rental-detail", args=[other_rental.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.other_user.id)
