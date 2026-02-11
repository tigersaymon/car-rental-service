from celery import shared_task
from django.utils import timezone

from notifications.messages import message_overdue_rental
from notifications.services.telegram import send_telegram_message
from rental.models import Rental


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
)
def notify_overdue_rentals(self):
    """
    Notify via Telegram about rentals that are overdue.
    Updates rental status and calculates days late.
    """
    today = timezone.localdate()

    overdue_rentals = Rental.objects.select_related("user", "car").filter(
        end_date__lt=today,
        actual_return_date__isnull=True,
        status=Rental.Status.BOOKED,
    )

    for rental in overdue_rentals:
        Rental.objects.filter(pk=rental.pk).update(status=Rental.Status.OVERDUE)
        days_late = (today - rental.end_date).days
        telegram_message = message_overdue_rental(rental, days_late)
        send_telegram_message(telegram_message)
