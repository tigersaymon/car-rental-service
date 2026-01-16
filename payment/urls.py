from django.urls import path
from .views import (
    StripeWebhookAPIView,
    PaymentSuccessAPIView,
    PaymentCancelAPIView,
    CreateRentalPaymentAPIView,
)

app_name = "payment"

urlpatterns = [
    path("stripe/webhook/", StripeWebhookAPIView.as_view(), name="stripe-webhook"),
    path("success/", PaymentSuccessAPIView.as_view(), name="success"),
    path("cancel/", PaymentCancelAPIView.as_view(), name="cancel"),
    path("rental/<int:rental_id>/payment/", CreateRentalPaymentAPIView.as_view(), name="create-rental-payment"),
]
