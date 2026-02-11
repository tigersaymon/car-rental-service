from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from notifications.messages import message_expired_payment
from notifications.services.telegram import send_telegram_message
from payment.models import Payment


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def expire_pending_payments(self):
    """
    Expire payments that are pending for more than 24 hours.
    Sends a Telegram notification for each expired payment.
    """
    now = timezone.now()
    expiration_threshold = now - timedelta(hours=24)

    pending_payments = Payment.objects.filter(
        status=Payment.Status.PENDING, created_at__lte=expiration_threshold
    ).select_related("rental__user", "rental__car")

    for payment in pending_payments:
        payment.status = Payment.Status.EXPIRED
        payment.save(update_fields=["status"])
        telegram_message = message_expired_payment(payment)
        send_telegram_message(telegram_message)
