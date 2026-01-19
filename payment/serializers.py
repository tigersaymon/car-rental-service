from rest_framework import serializers

from payment.models import Payment
from rental.serializers import RentalDetailSerializer


class PaymentListSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model (List View).

    Provides a summary of the payment, including:
    - ID, Type, Status, Amount.
    - Session URL for Stripe.
    - Rental ID (for reference).
    """

    class Meta:
        model = Payment
        fields = [
            "id",
            "type",
            "status",
            "money_to_pay",
            "session_url",
            "created_at",
            "rental",
        ]


class PaymentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for the Payment model (Detail View).

    Provides full details of the payment, including:
    - A nested 'rental' object with full car and user details.
    - Stripe Session ID.
    """

    rental = RentalDetailSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "type",
            "status",
            "money_to_pay",
            "session_url",
            "session_id",
            "created_at",
            "rental",
        ]
