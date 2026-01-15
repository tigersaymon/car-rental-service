from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CarViewSet


router = DefaultRouter()
router.register("cars", CarViewSet, basename="car")

urlpatterns = [path("", include(router.urls))]


app_name = "car"
