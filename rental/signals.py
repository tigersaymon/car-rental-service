from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.tasks import notify_new_rental
from rental.models import Rental


@receiver(post_save, sender=Rental)
def send_new_rental_notification(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: notify_new_rental.delay(instance.id))
