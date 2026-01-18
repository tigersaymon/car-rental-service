class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model.

    Represents a payment created for a rental, including:
    - payment type (rental, cancellation fee, overdue fee)
    - current payment status
    - amount to be paid
    - Stripe Checkout session URL
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
        ]
