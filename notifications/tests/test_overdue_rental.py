from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from car.models import Car
from rental.models import Rental
from notifications.tasks.overdue_rentals import notify_overdue_rentals


User = get_user_model()


class NotifyOverdueRentalsTaskTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123"
        )

        self.car = Car.objects.create(
            brand="BMW",
            model="X5",
            year=2022,
            daily_rate=100,
            inventory=5,
        )

    def _create_valid_rental(self, **kwargs):
        return Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.today,
            end_date=self.today + timedelta(days=1),
            **kwargs
        )

    @patch("notifications.tasks.overdue_rentals.send_telegram_message")
    def test_overdue_rental_becomes_overdue_and_sends_notification(
            self,
            mock_send
    ):
        rental = self._create_valid_rental(status=Rental.Status.BOOKED)

        Rental.objects.filter(pk=rental.pk).update(
            end_date=self.today - timedelta(days=2)
        )

        notify_overdue_rentals()

        rental.refresh_from_db()

        self.assertEqual(rental.status, Rental.Status.OVERDUE)
        mock_send.assert_called_once()

        message = mock_send.call_args[0][0]
        self.assertIn("Rental Overdue", message)
        self.assertIn(self.user.email, message)
        self.assertIn("Days late: 2", message)

    @patch("notifications.services.telegram.send_telegram_message")
    def test_completed_rental_is_ignored(self, mock_send):
        rental = self._create_valid_rental(status=Rental.Status.COMPLETED)

        Rental.objects.filter(pk=rental.pk).update(
            end_date=self.today - timedelta(days=1)
        )

        notify_overdue_rentals()

        rental.refresh_from_db()

        self.assertEqual(rental.status, Rental.Status.COMPLETED)
        mock_send.assert_not_called()

    @patch("notifications.services.telegram.send_telegram_message")
    def test_rental_with_actual_return_date_is_ignored(self, mock_send):
        rental = self._create_valid_rental(
            status=Rental.Status.BOOKED,
            actual_return_date=self.today
        )

        Rental.objects.filter(pk=rental.pk).update(
            end_date=self.today - timedelta(days=3)
        )

        notify_overdue_rentals()

        rental.refresh_from_db()

        self.assertEqual(rental.status, Rental.Status.BOOKED)
        mock_send.assert_not_called()

    @patch("notifications.services.telegram.send_telegram_message")
    def test_future_rental_is_ignored(self, mock_send):
        rental = self._create_valid_rental(status=Rental.Status.BOOKED)

        notify_overdue_rentals()

        rental.refresh_from_db()

        self.assertEqual(rental.status, Rental.Status.BOOKED)
        mock_send.assert_not_called()
