from celery import shared_task

from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def notify_rental_cancelled(self, rental_id: int):
    try:
        rental = Rental.objects.select_related("user", "car").get(id=rental_id)
    except Rental.DoesNotExist:
        return

    text = (
        "❌ <b>Rental Cancelled</b>\n"
        f"User: {rental.user.email}\n"
        f"Car: {rental.car}\n"
        f"Period: {rental.start_date} → {rental.end_date}"
    )

    send_telegram_message(text)
