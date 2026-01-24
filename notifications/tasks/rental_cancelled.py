from celery import shared_task

from notifications.messages import message_cancelled_rental
from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def notify_rental_cancelled(self, rental_id: int):
    """
    Notify via Telegram when a rental is cancelled.
    Fetches rental by ID and sends a notification message.
    """
    try:
        rental = Rental.objects.select_related("user", "car").get(id=rental_id)
    except Rental.DoesNotExist:
        return

    telegram_message = message_cancelled_rental(rental)
    send_telegram_message(telegram_message)
