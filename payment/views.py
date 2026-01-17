# payment/views.py
import os
import stripe
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from notifications.tasks import notify_successful_payment
from rental.models import Rental
from payment.models import Payment
from payment.services import create_stripe_payment_for_rental


WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookAPIView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=WEBHOOK_SECRET,
            )
        except ValueError:
            return Response(status=400)
        except stripe.error.SignatureVerificationError:
            return Response(status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            payment = Payment.objects.filter(session_id=session["id"]).first()
            if payment:
                payment.status = Payment.Status.PAID
                payment.save(update_fields=["status"])
                notify_successful_payment.delay(payment.id)

        return Response(status=200)


class PaymentSuccessAPIView(APIView):
    permission_classes = []

    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response({"detail": "Missing session_id"}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(session_id=session_id).first()
        if not payment:
            return Response({"detail": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "Payment successful", "payment_id": payment.id})


class PaymentCancelAPIView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({
            "detail": (
                "Payment was cancelled. "
                "You can complete it later — session valid for 24 hours."
            )
        })


class CreateRentalPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, rental_id):
        rental = get_object_or_404(Rental, id=rental_id)

        payment = create_stripe_payment_for_rental(
            rental=rental,
            payment_type=Payment.Type.RENTAL,
            request=request
        )

        return Response({
            "payment_id": payment.id,
            "money_to_pay": str(payment.money_to_pay),
            "status": payment.status,
            "session_url": payment.session_url
        }, status=status.HTTP_200_OK)
