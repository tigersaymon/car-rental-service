from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CreateRentalPaymentAPIView,
    PaymentCancelAPIView,
    PaymentSuccessAPIView,
    PaymentViewSet,
    StripeWebhookAPIView,
)


router = DefaultRouter()
router.register("", PaymentViewSet, basename="payment")

urlpatterns = [
    path("stripe/webhook/", StripeWebhookAPIView.as_view(), name="stripe-webhook"),
    path("success/", PaymentSuccessAPIView.as_view(), name="success"),
    path("cancel/", PaymentCancelAPIView.as_view(), name="cancel"),
    path("rental/<int:rental_id>/payment/", CreateRentalPaymentAPIView.as_view(), name="create-rental-payment"),
    path("", include(router.urls)),
]


app_name = "payment"
