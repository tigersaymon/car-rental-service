from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from car.models import Car
from notifications.tasks.expire_payments import expire_pending_payments
from payment.models import Payment
from rental.models import Rental


User = get_user_model()


class ExpirePendingPaymentsTaskTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = User.objects.create_user(email="test@example.com", password="password123")

        self.car = Car.objects.create(
            brand="BMW",
            model="X5",
            year=2022,
            daily_rate=100,
            inventory=5,
        )

        self.rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.now.date(),
            end_date=(self.now + timedelta(days=1)).date(),
        )

    @patch("notifications.tasks.expire_payments.send_telegram_message")
    def test_expire_pending_payment_changes_status_and_sends_notification(self, mock_send):
        old_payment = Payment.objects.create(
            rental=self.rental,
            status=Payment.Status.PENDING,
            type=Payment.Type.RENTAL,
            session_url="http://example.com/session",
            session_id="sess_123",
            money_to_pay=100,
        )

        expired_date = timezone.now() - timedelta(hours=25)
        Payment.objects.filter(id=old_payment.id).update(created_at=expired_date)

        expire_pending_payments()
        old_payment.refresh_from_db()
        self.assertEqual(old_payment.status, Payment.Status.EXPIRED)

    @patch("notifications.tasks.expire_payments.send_telegram_message")
    def test_paid_payment_is_not_expired(self, mock_send):
        paid_payment = Payment.objects.create(
            rental=self.rental,
            status=Payment.Status.PAID,
            type=Payment.Type.RENTAL,
            session_url="http://example.com/session",
            session_id="sess_456",
            money_to_pay=150,
            created_at=self.now - timedelta(hours=25),
        )

        expire_pending_payments()

        paid_payment.refresh_from_db()
        self.assertEqual(paid_payment.status, Payment.Status.PAID)
        mock_send.assert_not_called()

    @patch("notifications.tasks.expire_payments.send_telegram_message")
    def test_recent_pending_payment_is_not_expired(self, mock_send):
        recent_payment = Payment.objects.create(
            rental=self.rental,
            status=Payment.Status.PENDING,
            type=Payment.Type.RENTAL,
            session_url="http://example.com/session",
            session_id="sess_789",
            money_to_pay=200,
            created_at=self.now - timedelta(hours=1),
        )

        expire_pending_payments()

        recent_payment.refresh_from_db()
        self.assertEqual(recent_payment.status, Payment.Status.PENDING)
        mock_send.assert_not_called()
