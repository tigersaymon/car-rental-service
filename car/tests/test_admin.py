from django.contrib import admin
from django.test import TestCase

from car.admin import CarAdmin
from car.models import Car


class CarAdminTests(TestCase):
    """Tests for CarAdmin configuration."""

    def setUp(self):
        """Initialize CarAdmin instance for testing."""
        self.model_admin = CarAdmin(Car, admin.site)

    def test_list_display(self):
        """Ensure list_display contains expected fields."""
        expected = ("brand", "model", "year", "daily_rate", "inventory")
        self.assertEqual(self.model_admin.list_display, expected)

    def test_list_filter(self):
        """Ensure list_filter contains expected fields."""
        expected = ("brand", "fuel_type")
        self.assertEqual(self.model_admin.list_filter, expected)
