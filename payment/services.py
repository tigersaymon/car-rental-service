from decimal import Decimal

import stripe
from django.conf import settings
from django.urls import reverse

from payment.models import Payment
from rental.models import Rental


FINE_MULTIPLIER = Decimal("1.5")


def create_stripe_payment_for_rental(
    *,
    rental: Rental,
    payment_type: Payment.Type,
    request,
) -> Payment:
    """
    Creates a Stripe Checkout Session and a corresponding local Payment record.

    This function communicates with Stripe API to generate a payment link
    and saves the session ID to the database for future verification via webhooks.

    Args:
        rental (Rental): The rental instance associated with the payment.
        payment_type (Payment.Type): The type of payment (RENTAL, OVERDUE, etc.).
        request (HttpRequest): The request object used to build absolute URLs for callbacks.

    Returns:
        Payment: The created Payment instance containing the session URL.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    amount = _calculate_amount(rental=rental, payment_type=payment_type)

    success_url = request.build_absolute_uri(reverse("payment:success")) + "?session_id={CHECKOUT_SESSION_ID}"

    cancel_url = request.build_absolute_uri(reverse("payment:cancel"))

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Rental #{rental.id} — {payment_type}",
                    },
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    payment = Payment.objects.create(
        rental=rental,
        type=payment_type,
        session_id=session.id,
        session_url=session.url,
        money_to_pay=amount,
    )

    return payment


def _calculate_amount(*, rental: Rental, payment_type: Payment.Type) -> Decimal:
    """
    Calculates the exact amount to be paid based on rental duration and type.

    Logic:
    - RENTAL: Standard rate * days (min 1 day).
    - CANCELLATION_FEE: 50% of the standard rental price.
    - OVERDUE_FEE: (Overdue days * daily rate * 1.5 multiplier).

    Args:
        rental (Rental): The rental object.
        payment_type (Payment.Type): The type of fee to calculate.

    Returns:
        Decimal: The calculated amount rounded to 2 decimal places.

    Raises:
        ValueError: If 'actual_return_date' is missing for OVERDUE_FEE or type is invalid.
    """
    daily_rate = rental.car.daily_rate

    rental_days = max((rental.end_date - rental.start_date).days + 1, 1)
    base_price = Decimal(rental_days) * daily_rate

    if payment_type == Payment.Type.RENTAL:
        return base_price

    if payment_type == Payment.Type.CANCELLATION_FEE:
        return (base_price * Decimal("0.5")).quantize(Decimal("0.01"))

    if payment_type == Payment.Type.OVERDUE_FEE:
        if not rental.actual_return_date:
            raise ValueError("Cannot calculate overdue fee without actual_return_date")
        overdue_days = max((rental.actual_return_date - rental.end_date).days, 0)
        return (Decimal(overdue_days) * daily_rate * FINE_MULTIPLIER).quantize(Decimal("0.01"))

    raise ValueError("Unsupported payment type")


def complete_rental_if_all_payments_paid(payment: Payment) -> None:
    """
    Checks if all payments for a rental are settled and updates rental status.

    - If it's a CANCELLATION_FEE, immediately cancels the rental.
    - If it's a standard payment, checks for other pending payments.
    - If no pending payments remain, marks the rental as COMPLETED.

    Args:
        payment (Payment): The payment that was just successfully processed.
    """
    rental = payment.rental

    if payment.type == Payment.Type.CANCELLATION_FEE:
        rental.status = Rental.Status.CANCELLED
        rental.save(update_fields=["status"])
        return

    if rental.status in [Rental.Status.COMPLETED, Rental.Status.CANCELLED]:
        return

    has_pending_payments = (
        Payment.objects.filter(rental=rental, status=Payment.Status.PENDING).exclude(id=payment.id).exists()
    )

    if not has_pending_payments:
        rental.status = Rental.Status.COMPLETED
        rental.save(update_fields=["status"])
