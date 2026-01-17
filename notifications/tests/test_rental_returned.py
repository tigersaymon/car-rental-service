from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from car.models import Car
from notifications.tasks.rental_returned import notify_rental_returned
from rental.models import Rental


User = get_user_model()


class RentalReturnNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="return_test@example.com", password="password123")
        self.car = Car.objects.create(brand="Tesla", model="Model 3", year=2023, daily_rate=150, inventory=5)

        self.rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timezone.timedelta(days=2)).date(),
            status=Rental.Status.BOOKED,
        )

    @patch("notifications.tasks.rental_returned.send_telegram_message")
    def test_notify_rental_returned_success(self, mock_send):
        self.rental.actual_return_date = timezone.now().date()
        self.rental.save()

        notify_rental_returned(self.rental.id)

        mock_send.assert_called_once()

        args, _ = mock_send.call_args
        message_text = args[0]

        self.assertIn("✅ <b>Rental Returned</b>", message_text)
        self.assertIn(self.user.email, message_text)
        self.assertIn("Tesla Model 3", message_text)
        self.assertIn(str(self.rental.actual_return_date), message_text)
        self.assertIn(str(self.rental.status), message_text)

    @patch("notifications.tasks.rental_returned.send_telegram_message")
    def test_notify_rental_returned_not_found(self, mock_send):
        notify_rental_returned(999)

        mock_send.assert_not_called()
