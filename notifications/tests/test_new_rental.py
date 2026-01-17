from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from car.models import Car
from notifications.tasks.new_rental import notify_new_rental
from rental.models import Rental
from user.models import User


class NewRentalTaskTest(TestCase):
    def test_notify_new_rental(self):
        user = User.objects.create_user(email="test@test.com", password="12345678")
        car = Car.objects.create(brand="Toyota", model="Camry", year=2020, fuel_type="GAS", daily_rate=100, inventory=3)

        rental = Rental.objects.create(
            user=user,
            car=car,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=3),
            status=Rental.Status.BOOKED,
        )

        with patch("notifications.tasks.new_rental.send_telegram_message") as mock_send:
            notify_new_rental(rental.id)

            mock_send.assert_called_once()
            sent_text = mock_send.call_args[0][0]
            self.assertIn("New Rental Created", sent_text)
            self.assertIn(user.email, sent_text)
            self.assertIn(car.model, sent_text)
            self.assertIn(str(rental.start_date), sent_text)
            self.assertIn(str(rental.end_date), sent_text)
