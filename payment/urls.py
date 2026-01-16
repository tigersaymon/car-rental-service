from django.urls import path
from .views import (
    StripeWebhookView,
    PaymentSuccessView,
    PaymentCancelView,
    CreateRentalPaymentView,
)

app_name = "payment"

urlpatterns = [
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("success/", PaymentSuccessView.as_view(), name="success"),
    path("cancel/", PaymentCancelView.as_view(), name="cancel"),
    path(
        "rental/<int:rental_id>/payment/",
        CreateRentalPaymentView.as_view(),
        name="create-rental-payment"
    ),
]
