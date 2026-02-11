from celery import shared_task

from notifications.messages import message_successful_payment
from notifications.services.telegram import send_telegram_message
from payment.models import Payment


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def notify_successful_payment(self, payment_id: int):
    """
    Notify via Telegram when a payment is successful.
    Fetches payment by ID and sends a notification message.
    """
    try:
        payment = Payment.objects.select_related("rental__user", "rental__car").get(id=payment_id)
    except Payment.DoesNotExist:
        return

    telegram_message = message_successful_payment(payment)
    send_telegram_message(telegram_message)
