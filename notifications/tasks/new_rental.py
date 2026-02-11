from celery import shared_task

from notifications.messages import message_new_rental
from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 10})
def notify_new_rental(self, rental_id: int):
    """
    Notify via Telegram when a new rental is created.
    Fetches rental by ID and sends a notification message.
    """
    try:
        rental = Rental.objects.select_related("user", "car").get(id=rental_id)
        telegram_message = message_new_rental(rental)
        send_telegram_message(telegram_message)

    except Rental.DoesNotExist:
        return
