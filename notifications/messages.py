def message_expired_payment(payment):
    """
    Build a notification message for an expired payment.
    Includes user, car, payment type and amount.
    """
    return (
        "⚠️ <b>Payment Expired</b>\n"
        f"User: {payment.rental.user.email}\n"
        f"Car: {payment.rental.car}\n"
        f"Type: {payment.type}\n"
        f"Amount: ${payment.money_to_pay}\n"
    )


def message_successful_payment(payment):
    """
    Build a notification message for a successful payment.
    Shows user, car, payment type and amount.
    """
    return (
        "💰 <b>Payment Successful</b>\n"
        f"User: {payment.rental.user.email}\n"
        f"Car: {payment.rental.car}\n"
        f"Type: {payment.type}\n"
        f"Amount: ${payment.money_to_pay}\n"
    )


def message_new_rental(rental):
    """
    Build a notification message for a new rental.
    Contains rental period and current status.
    """
    return (
        "🚗 <b>New Rental Created</b>\n"
        f"User: {rental.user.email}\n"
        f"Car: {rental.car}\n"
        f"Period: {rental.start_date} → {rental.end_date}\n"
        f"Status: {rental.status}"
    )


def message_overdue_rental(rental, days_late: int):
    """
    Build a notification message for an overdue rental.
    Shows end date and number of overdue days.
    """
    return (
        "⏰ <b>Rental Overdue</b>\n"
        f"User: {rental.user.email}\n"
        f"Car: {rental.car}\n"
        f"End date: {rental.end_date}\n"
        f"Days late: {days_late}"
    )


def message_cancelled_rental(rental):
    """
    Build a notification message for a cancelled rental.
    Includes rental period and car information.
    """
    return (
        "❌ <b>Rental Cancelled</b>\n"
        f"User: {rental.user.email}\n"
        f"Car: {rental.car}\n"
        f"Period: {rental.start_date} → {rental.end_date}"
    )


def message_returned_rental(rental):
    """
    Build a notification message for a returned rental.
    Shows actual return date and final status.
    """
    return (
        "✅ <b>Rental Returned</b>\n"
        f"User: {rental.user.email}\n"
        f"Car: {rental.car}\n"
        f"Returned at: {rental.actual_return_date}\n"
        f"Status: {rental.status}"
    )
