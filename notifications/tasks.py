from celery import shared_task

from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 10}
)
def notify_new_rental(self, rental_id: int):
    try:
        rental = (
            Rental.objects
            .select_related("user", "car")
            .get(id=rental_id)
        )

        text = (
            "🚗 <b>New Rental Created</b>\n"
            f"User: {rental.user.email}\n"
            f"Car: {rental.car}\n"
            f"Period: {rental.start_date} → {rental.end_date}\n"
            f"Status: {rental.status}"
        )

        send_telegram_message(text)

    except Rental.DoesNotExist:
        return
