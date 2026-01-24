from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from car.models import Car
from notifications.tasks.rental_cancelled import notify_rental_cancelled
from rental.models import Rental


User = get_user_model()


class RentalNotificationTests(TestCase):
    """
    Tests the notify_rental_cancelled Celery task.
    Ensures Telegram notifications are sent correctly when rentals are cancelled.
    """

    def setUp(self):
        """Set up user, car, and rental for testing notifications."""
        self.user = User.objects.create_user(email="user@test.com", password="password")
        self.car = Car.objects.create(brand="Tesla", model="Model S", year=2023, daily_rate=150, inventory=2)

        today = timezone.localdate()
        self.rental = Rental.objects.create(
            user=self.user, car=self.car, start_date=today, end_date=today + timedelta(days=5)
        )

    @patch("notifications.tasks.rental_cancelled.send_telegram_message")
    def test_notify_rental_cancelled_success(self, mock_send):
        """Cancelled rental triggers a Telegram notification with correct details."""
        notify_rental_cancelled(self.rental.id)

        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        message_text = args[0]

        self.assertIn("❌ <b>Rental Cancelled</b>", message_text)
        self.assertIn(self.user.email, message_text)
        self.assertIn("Tesla Model S", message_text)

        today = timezone.localdate()
        expected_period = f"{today} → {today + timedelta(days=5)}"
        self.assertIn(expected_period, message_text)

    @patch("notifications.tasks.rental_cancelled.send_telegram_message")
    def test_notify_rental_cancelled_not_found(self, mock_send):
        """Nonexistent rental ID does not trigger any Telegram notification."""
        notify_rental_cancelled(9999)

        mock_send.assert_not_called()
