from celery import shared_task

from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def notify_rental_returned(self, rental_id: int):
    try:
        rental = Rental.objects.select_related("user", "car").get(id=rental_id)
    except Rental.DoesNotExist:
        return

    text = (
        "✅ <b>Rental Returned</b>\n"
        f"User: {rental.user.email}\n"
        f"Car: {rental.car}\n"
        f"Returned at: {rental.actual_return_date}\n"
        f"Status: {rental.status}"
    )

    send_telegram_message(text)
