from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import ANY, MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from car.models import Car
from payment.models import Payment
from rental.models import Rental
from user.models import User


class BasePaymentViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="testpass")

        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.car = Car.objects.create(
            brand="TestBrand",
            model="X1",
            year=2023,
            fuel_type="GAS",
            daily_rate=Decimal("100.00"),
            inventory=1,
        )

        self.rental = Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=3),
        )


class TestCreateRentalPaymentAPIView(BasePaymentViewTest):
    @patch("payment.views.create_stripe_payment_for_rental")
    def test_calls_service_and_returns_payment_data(self, mock_service):
        """Tests that the endpoint calls the service and returns correct payment data."""
        mock_payment = MagicMock()
        mock_payment.id = 42
        mock_payment.money_to_pay = Decimal("300.00")
        mock_payment.status = Payment.Status.PENDING
        mock_payment.session_url = "http://stripe.test/session"

        mock_service.return_value = mock_payment

        url = reverse(
            "payment:create-rental-payment",
            kwargs={"rental_id": self.rental.id},
        )
        response = self.client.post(url)

        mock_service.assert_called_once_with(
            rental=self.rental,
            payment_type=Payment.Type.RENTAL,
            request=ANY,  # приймаємо будь-який request
        )

        assert response.data["session_url"] == mock_payment.session_url
        assert response.data["money_to_pay"] == "300.00"


class TestPaymentSuccessAPIView(BasePaymentViewTest):
    def test_missing_session_id_returns_400(self):
        """Tests that requests without session_id return 400 Bad Request."""
        url = reverse("payment:success")
        response = self.client.get(url)

        assert response.status_code == 400

    def test_payment_not_found_returns_404(self):
        """Tests that invalid session_id returns 404 Not Found."""
        url = reverse("payment:success")
        response = self.client.get(url, {"session_id": "invalid"})

        assert response.status_code == 404

    def test_existing_payment_returns_success(self):
        """Tests that a valid session_id returns payment details."""
        payment = Payment.objects.create(
            rental=self.rental,
            type=Payment.Type.RENTAL,
            session_id="sess_123",
            session_url="http://stripe.test",
            money_to_pay=Decimal("300.00"),
        )

        url = reverse("payment:success")
        response = self.client.get(url, {"session_id": payment.session_id})

        assert response.status_code == 200
        assert response.data["payment_id"] == payment.id


class TestPaymentCancelAPIView(BasePaymentViewTest):
    def test_cancel_payment_endpoint_works(self):
        """Tests that the cancel endpoint returns a user-friendly message."""
        url = reverse("payment:cancel")
        response = self.client.get(url)

        assert response.status_code == 200


class TestStripeWebhookAPIView(BasePaymentViewTest):
    @patch("payment.views.complete_rental_if_all_payments_paid")
    @patch("payment.views.notify_successful_payment.delay")
    @patch("payment.views.stripe.Webhook.construct_event")
    def test_checkout_session_completed_marks_payment_paid(
        self,
        mock_construct_event,
        mock_notify,
        mock_complete_rental,
    ):
        """Tests processing of a valid Stripe webhook event."""
        payment = Payment.objects.create(
            rental=self.rental,
            type=Payment.Type.RENTAL,
            session_id="sess_123",
            session_url="http://stripe.test",
            money_to_pay=Decimal("300.00"),
        )

        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "sess_123"}},
        }

        url = reverse("payment:stripe-webhook")
        self.client.post(
            url,
            data={},
            HTTP_STRIPE_SIGNATURE="test",
            format="json",
        )

        payment.refresh_from_db()

        assert payment.status == Payment.Status.PAID
        mock_notify.assert_called_once_with(payment.id)
        mock_complete_rental.assert_called_once_with(payment)

    @patch(
        "payment.views.stripe.Webhook.construct_event",
        side_effect=ValueError("Invalid payload"),
    )
    def test_invalid_webhook_signature_returns_400(self, _):
        """Tests that invalid Stripe signature returns 400 Bad Request."""
        url = reverse("payment:stripe-webhook")
        response = self.client.post(
            url,
            data={},
            HTTP_STRIPE_SIGNATURE="invalid",
            format="json",
        )

        assert response.status_code == 400
