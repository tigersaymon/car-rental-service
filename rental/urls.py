from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rental.views import RentalViewSet


router = DefaultRouter()
router.register("rentals", RentalViewSet, basename="rental")

urlpatterns = [path("", include(router.urls))]


app_name = "rental"
