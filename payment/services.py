def create_stripe_payment_for_rental(rental, payment_type, request):
    """
    Temporary stub for payment service.
    TODO: Implement real Stripe logic here.
    """

    class FakeSession:
        session_url = "https://fake.stripe.url/test"

    return FakeSession()