from celery import shared_task
from django.utils import timezone

from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
)
def notify_overdue_rentals(self):
    today = timezone.localdate()

    overdue_rentals = Rental.objects.select_related("user", "car").filter(
        end_date__lt=today,
        actual_return_date__isnull=True,
        status=Rental.Status.BOOKED,
    )

    for rental in overdue_rentals:
        Rental.objects.filter(pk=rental.pk).update(status=Rental.Status.OVERDUE)

        text = (
            "⏰ <b>Rental Overdue</b>\n"
            f"User: {rental.user.email}\n"
            f"Car: {rental.car}\n"
            f"End date: {rental.end_date}\n"
            f"Days late: {(today - rental.end_date).days}"
        )

        send_telegram_message(text)
