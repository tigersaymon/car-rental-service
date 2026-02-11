from django.db import transaction
from django.db.models.base import ModelBase
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.tasks import notify_new_rental
from rental.models import Rental


@receiver(post_save, sender=Rental)
def send_new_rental_notification(sender: ModelBase, instance: Rental, created: bool, **kwargs) -> None:
    """
    Signal receiver that triggers a Celery task to send a notification
    when a new Rental is created.

    Wrapped in transaction.on_commit to ensure the DB record exists
    before the worker tries to process it.
    """
    if created:
        transaction.on_commit(lambda: notify_new_rental.delay(instance.id))
