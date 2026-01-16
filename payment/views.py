import os
import stripe
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404

from rental.models import Rental
from payment.models import Payment
from payment.services import create_stripe_payment_for_rental


WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):

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
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            payment = Payment.objects.filter(session_id=session["id"]).first()
            if payment:
                payment.status = Payment.Status.PAID
                payment.save(update_fields=["status"])

        return HttpResponse(status=200)


class PaymentSuccessView(View):

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("session_id")
        if not session_id:
            return JsonResponse({"detail": "Missing session_id"}, status=400)

        payment = Payment.objects.filter(session_id=session_id).first()
        if not payment:
            return JsonResponse({"detail": "Payment not found"}, status=404)

        return JsonResponse(
            {"detail": "Payment successful", "payment_id": payment.id}
        )


class PaymentCancelView(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "detail": (
                    "Payment was cancelled. "
                    "You can complete it later — session valid for 24 hours."
                )
            }
        )


class CreateRentalPaymentView(View):
    def post(self, request, rental_id, *args, **kwargs):
        rental = get_object_or_404(Rental, id=rental_id)

        payment = create_stripe_payment_for_rental(
            rental=rental,
            payment_type=Payment.Type.RENTAL,
            request=request
        )

        return JsonResponse({
            "payment_id": payment.id,
            "money_to_pay": str(payment.money_to_pay),
            "status": payment.status,
            "session_url": payment.session_url
        })
