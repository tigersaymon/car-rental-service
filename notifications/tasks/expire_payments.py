from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from notifications.services.telegram import send_telegram_message
from payment.models import Payment


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def expire_pending_payments(self):
    now = timezone.now()
    expiration_threshold = now - timedelta(hours=24)

    pending_payments = Payment.objects.filter(
        status=Payment.Status.PENDING, created_at__lte=expiration_threshold
    ).select_related("rental__user", "rental__car")

    for payment in pending_payments:
        payment.status = Payment.Status.EXPIRED
        payment.save(update_fields=["status"])

        text = (
            f"⚠️ <b>Payment Expired</b>\n"
            f"User: {payment.rental.user.email}\n"
            f"Car: {payment.rental.car}\n"
            f"Type: {payment.type}\n"
            f"Amount: ${payment.money_to_pay}\n"
        )
        send_telegram_message(text)
