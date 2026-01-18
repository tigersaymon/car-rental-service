from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from car.models import Car
from payment import services
from payment.models import Payment
from rental.models import Rental
from user.models import User


class PaymentServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="1234")
        self.car = Car.objects.create(
            brand="BMW",
            model="X5",
            year=2023,
            fuel_type="GAS",
            daily_rate=100,
            inventory=1
        )
        self.rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2)
        )

    def test_calculate_amount_various(self):

        amount = services._calculate_amount(rental=self.rental, payment_type=Payment.Type.RENTAL)
        self.assertEqual(amount, Decimal("300.00"))

        amount = services._calculate_amount(rental=self.rental, payment_type=Payment.Type.CANCELLATION_FEE)
        self.assertEqual(amount, Decimal("150.00"))

        self.rental.actual_return_date = self.rental.end_date + timedelta(days=1)
        amount = services._calculate_amount(rental=self.rental, payment_type=Payment.Type.OVERDUE_FEE)
        self.assertEqual(amount, Decimal("150.00"))  # 1 day overdue * 100 * 1.5

    def test_calculate_amount_overdue_without_actual_return_raises(self):
        with self.assertRaises(ValueError):
            services._calculate_amount(rental=self.rental, payment_type=Payment.Type.OVERDUE_FEE)

    def test_calculate_amount_invalid_payment_type_raises(self):
        with self.assertRaises(ValueError):
            services._calculate_amount(rental=self.rental, payment_type="INVALID")

    @patch("payment.services.stripe.checkout.Session.create")
    def test_create_stripe_payment_for_rental(self, mock_session):
        mock_session.return_value.id = "sess_123"
        mock_session.return_value.url = "http://stripe.test"

        class DummyRequest:
            def build_absolute_uri(self, path):
                return f"http://testserver{path}"

        payment = services.create_stripe_payment_for_rental(
            rental=self.rental,
            payment_type=Payment.Type.RENTAL,
            request=DummyRequest()
        )

        self.assertEqual(payment.rental, self.rental)
        self.assertEqual(payment.type, Payment.Type.RENTAL)
        self.assertEqual(payment.session_id, "sess_123")
        self.assertEqual(payment.session_url, "http://stripe.test")
        self.assertEqual(payment.money_to_pay, Decimal("300.00"))
        mock_session.assert_called_once()

    def test_complete_rental_status_various(self):
        scenarios = [
            ("BOOKED", Payment.Type.RENTAL, False, "COMPLETED"),
            ("BOOKED", Payment.Type.CANCELLATION_FEE, False, "CANCELLED"),
            ("COMPLETED", Payment.Type.RENTAL, False, "COMPLETED"),
            ("BOOKED", Payment.Type.RENTAL, True, "BOOKED"),
        ]
        for existing_status, payment_type, pending_payments, expected_status in scenarios:
            self.rental.status = existing_status
            self.rental.save()

            Payment.objects.filter(rental=self.rental).delete()

            if pending_payments:
                Payment.objects.create(
                    rental=self.rental,
                    type=Payment.Type.RENTAL,
                    status=Payment.Status.PENDING,
                    session_id="sess_pending",
                    session_url="http://stripe.test",
                    money_to_pay=Decimal("100.00")
                )

            payment = Payment.objects.create(
                rental=self.rental,
                type=payment_type,
                status=Payment.Status.PAID,
                session_id="sess_123",
                session_url="http://stripe.test",
                money_to_pay=Decimal("100.00")
            )

            services.complete_rental_if_all_payments_paid(payment)
            self.rental.refresh_from_db()
            self.assertEqual(self.rental.status, expected_status)
