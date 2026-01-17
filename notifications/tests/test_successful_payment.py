from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from car.models import Car
from notifications.tasks.successful_payment import notify_successful_payment
from payment.models import Payment
from rental.models import Rental
from user.models import User


class SuccessfulPaymentTaskTest(TestCase):
    def test_notify_successful_payment(self):
        user = User.objects.create_user(email="test@test.com", password="12345678")

        car = Car.objects.create(brand="Toyota", model="Camry", year=2020, fuel_type="GAS", daily_rate=100, inventory=3)

        rental = Rental.objects.create(
            user=user,
            car=car,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=2),
            status=Rental.Status.BOOKED,
        )

        payment = Payment.objects.create(
            rental=rental,
            status=Payment.Status.PAID,
            type=Payment.Type.RENTAL,
            money_to_pay=200,
        )

        with patch("notifications.tasks.successful_payment.send_telegram_message") as mock_send:
            notify_successful_payment(payment.id)

            mock_send.assert_called_once()
            sent_text = mock_send.call_args[0][0]
            self.assertIn("Payment Successful", sent_text)
            self.assertIn(str(payment.money_to_pay), sent_text)
            self.assertIn(user.email, sent_text)
            self.assertIn(car.model, sent_text)
