from django.test import SimpleTestCase
from django.urls import resolve, reverse

from car.views import CarViewSet


class CarUrlsTests(SimpleTestCase):
    """Tests for car app urls"""

    def test_car_list_url_resolves(self):
        """Check that car-list URL resolves to CarViewSet.list"""
        url = reverse("car:car-list")
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, CarViewSet.as_view({"get": "list"}).__name__)

    def test_car_detail_url_resolves(self):
        """Check that car-detail URL resolves to CarViewSet.retrieve"""
        url = reverse("car:car-detail", args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, CarViewSet.as_view({"get": "retrieve"}).__name__)
