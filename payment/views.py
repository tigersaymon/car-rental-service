import os

import stripe
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.tasks import notify_successful_payment
from payment.models import Payment
from payment.serializers import PaymentDetailSerializer, PaymentListSerializer
from payment.services import (
    complete_rental_if_all_payments_paid,
    create_stripe_payment_for_rental,
)
from rental.models import Rental


WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookAPIView(APIView):
    """
    Stripe webhook endpoint.

    Receives events from Stripe and processes completed checkout sessions.
    When a payment is successfully completed, marks the corresponding
    Payment as PAID and completes the Rental if all related payments are settled.
    """

    permission_classes = []

    @extend_schema(
        summary="Stripe webhook",
        description=(
            "Receives Stripe webhook events. "
            "Handles `checkout.session.completed` events to mark payments as PAID "
            "and complete the related rental if applicable."
        ),
        responses={200: None, 400: None},
    )
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
                complete_rental_if_all_payments_paid(payment)

        return Response(status=200)


class PaymentSuccessAPIView(APIView):
    """
    Payment success endpoint.

    Called by Stripe after a successful checkout.
    Returns basic information about the completed payment.
    """

    permission_classes = []

    @extend_schema(
        summary="Payment success callback",
        description="Returns payment information for a successful Stripe Checkout session.",
        responses={200: None, 400: None, 404: None},
    )
    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response(
                {"detail": "Missing session_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.filter(session_id=session_id).first()
        if not payment:
            return Response(
                {"detail": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"detail": "Payment successful", "payment_id": payment.id},
            status=status.HTTP_200_OK,
        )


class PaymentCancelAPIView(APIView):
    """
    Payment cancellation endpoint.

    Called when a user cancels the Stripe Checkout process.
    """

    permission_classes = []

    @extend_schema(
        summary="Payment cancelled",
        description="Indicates that the payment was cancelled by the user.",
        responses={200: None},
    )
    def get(self, request):
        return Response(
            {"detail": ("Payment was cancelled. You can complete it later — session valid for 24 hours.")},
            status=status.HTTP_200_OK,
        )


class CreateRentalPaymentAPIView(APIView):
    """
    Create rental payment endpoint.

    Creates a Stripe Checkout session for a rental payment
    and returns the payment details along with the session URL.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Create rental payment",
        description=(
            "Creates a Stripe Checkout session for the given rental "
            "and returns payment information including session URL."
        ),
        responses={200: None, 401: None, 404: None},
    )
    def post(self, request, rental_id):
        rental = get_object_or_404(Rental, id=rental_id)

        payment = create_stripe_payment_for_rental(
            rental=rental,
            payment_type=Payment.Type.RENTAL,
            request=request,
        )

        return Response(
            {
                "payment_id": payment.id,
                "money_to_pay": str(payment.money_to_pay),
                "status": payment.status,
                "session_url": payment.session_url,
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List all payments",
        description=(
            "Retrieves a list of payments.\n\n"
            "**Permissions:**\n"
            "- **Staff users**: Can see all payments in the system.\n"
            "- **Regular users**: Can only see payments related to their own rentals."
        ),
    ),
    retrieve=extend_schema(
        summary="Retrieve payment details",
        description=(
            "Retrieves detailed information about a specific payment.\n\n"
            "Includes nested rental information (Car details, dates, etc.)."
        ),
    ),
)
class PaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for viewing payments.
    Supports listing and retrieving individual payment details.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns the list of payments based on user role.
        - Staff: All payments.
        - User: Only payments linked to their rentals.
        Uses select_related to optimize DB queries.
        """
        queryset = Payment.objects.select_related("rental", "rental__car")
        user = self.request.user

        if user.is_staff:
            return queryset
        return queryset.filter(rental__user=user)

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class.
        - 'retrieve': PaymentDetailSerializer (includes nested rental).
        - 'list': PaymentListSerializer (lightweight).
        """
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentListSerializer
