from celery import shared_task

from notifications.services.telegram import send_telegram_message
from payment.models import Payment


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def notify_successful_payment(self, payment_id: int):
    try:
        payment = Payment.objects.select_related("rental__user", "rental__car").get(id=payment_id)
    except Payment.DoesNotExist:
        return

    text = (
        "💰 <b>Payment Successful</b>\n"
        f"User: {payment.rental.user.email}\n"
        f"Car: {payment.rental.car}\n"
        f"Type: {payment.type}\n"
        f"Amount: ${payment.money_to_pay}\n"
    )

    send_telegram_message(text)
