from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from notifications.tasks.rental_cancelled import notify_rental_cancelled
from notifications.tasks.rental_returned import notify_rental_returned
from payment.models import Payment
from payment.services import create_stripe_payment_for_rental

from .filters import RentalFilter
from .models import Rental
from .serializers import (
    RentalCreateSerializer,
    RentalDetailSerializer,
    RentalListSerializer,
    RentalReturnSerializer,
)


class RentalViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing Rentals.

    Provides capabilities to:
    - List and Retrieve rentals (filtered by user ownership).
    - Create new rentals with validation.
    - Return cars (generating payments).
    - Cancel rentals (calculating fees based on 24h rule).
    """

    queryset = Rental.objects.select_related("car", "user")
    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = RentalFilter

    def get_queryset(self) -> QuerySet[Rental]:
        """
        Returns rentals based on user role.
        - Staff users see all rentals.
        - Regular users see only their own rentals.
        """
        queryset = self.queryset
        user = self.request.user

        if user.is_staff:
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self) -> type[Serializer]:
        """
        Selects the appropriate serializer based on the action.
        """
        if self.action == "list":
            return RentalListSerializer
        if self.action == "retrieve":
            return RentalDetailSerializer
        if self.action == "create":
            return RentalCreateSerializer

        if self.action in ["return_car", "cancel_rental"]:
            return RentalReturnSerializer

        return RentalListSerializer

    @extend_schema(
        summary="Return a rented car",
        description="""
            Completes the rental process by fixing the return date.

            Logic:
            1. Sets `actual_return_date` to today.
            2. Generates a Stripe Payment session for the base rental cost.
            3. If the return is **late** (after `end_date`), creates an additional `OVERDUE_FEE` payment.
            4. Triggers a notification task.

            Note: The rental status does not change to COMPLETED immediately. It waits for the Stripe Webhook to confirm payment.
            """,
        request=None,
        responses={
            200: [
                OpenApiExample(
                    "Successful Return",
                    value={
                        "message": "Return registered. Please pay the invoice.",
                        "rental_payment_url": "https://checkout.stripe.com/c/pay/...",
                    },
                ),
                OpenApiExample(
                    "Late Return (Overdue)",
                    summary="Return with Overdue Fee",
                    value={
                        "message": "Car returned late. Please pay rental and overdue fee.",
                        "rental_payment_url": "https://checkout.stripe.com/c/pay/...",
                        "overdue_payment_url": "https://checkout.stripe.com/c/pay/...",
                    },
                ),
            ],
            400: OpenApiExample("Error", value={"error": "Rental is not active"}),
        },
    )
    @action(detail=True, methods=["POST"], url_path="return")
    def return_car(self, request, pk=None):
        rental = self.get_object()

        if rental.status not in [Rental.Status.BOOKED, Rental.Status.OVERDUE]:
            return Response({"error": "Rental is not active"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            rental.actual_return_date = timezone.now().date()
            rental.save()

            payment_rental = create_stripe_payment_for_rental(
                rental=rental, payment_type=Payment.Type.RENTAL, request=request
            )

            response_data = {
                "message": "Return registered. Please pay the invoice.",
                "rental_payment_url": payment_rental.session_url,
            }

            if rental.actual_return_date > rental.end_date:
                rental.status = Rental.Status.OVERDUE
                rental.save()

                payment_overdue = create_stripe_payment_for_rental(
                    rental=rental, payment_type=Payment.Type.OVERDUE_FEE, request=request
                )

                response_data["message"] = "Car returned late. Please pay rental and overdue fee."
                response_data["overdue_payment_url"] = payment_overdue.session_url

            transaction.on_commit(lambda: notify_rental_returned.delay(rental.id))

        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cancel a rental",
        description="""
            Cancels an active rental booking.

            Business Logic:
            - > 24 hours before start:** Free cancellation. Status changes to `CANCELLED` immediately.
            - < 24 hours before start:** Late cancellation fee applies.
              Generates a Stripe Payment session. Status changes to `CANCELLED` only after payment (via Webhook).
            """,
        request=None,
        responses={
            200: [
                OpenApiExample("Free Cancellation", value={"message": "Rental cancelled successfully"}),
                OpenApiExample(
                    "Late Cancellation (Fee required)",
                    summary="Late Cancellation",
                    value={
                        "message": "Late cancellation. Please pay the fee to cancel the reservation.",
                        "payment_url": "https://checkout.stripe.com/c/pay/...",
                    },
                ),
            ],
            400: OpenApiResponse(description="Cannot cancel this rental (e.g. already completed)"),
        },
    )
    @action(detail=True, methods=["POST"], url_path="cancel")
    def cancel_rental(self, request, pk=None):
        rental = self.get_object()

        if rental.status != Rental.Status.BOOKED:
            return Response({"error": "Cannot cancel this rental"}, status=status.HTTP_400_BAD_REQUEST)

        rental_start_dt = timezone.datetime.combine(rental.start_date, timezone.datetime.min.time())
        if timezone.is_aware(timezone.now()):
            rental_start_dt = timezone.make_aware(rental_start_dt)

        time_difference = rental_start_dt - timezone.now()

        if time_difference < timezone.timedelta(hours=24):
            payment = create_stripe_payment_for_rental(
                rental=rental, payment_type=Payment.Type.CANCELLATION_FEE, request=request
            )

            return Response(
                {
                    "message": "Late cancellation. Please pay the fee to cancel the reservation.",
                    "payment_url": payment.session_url,
                },
                status=status.HTTP_200_OK,
            )

        rental.status = Rental.Status.CANCELLED
        rental.save()

        transaction.on_commit(lambda: notify_rental_cancelled.delay(rental.id))

        return Response({"message": "Rental cancelled successfully"}, status=status.HTTP_200_OK)
