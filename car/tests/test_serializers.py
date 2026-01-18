from decimal import Decimal

from django.test import TestCase

from car.models import Car
from car.serializers import (
    CarDetailSerializer,
    CarImageSerializer,
    CarListSerializer,
    CarSerializer,
)


class CarSerializerTests(TestCase):
    """Tests for Car serializers"""

    def setUp(self):
        """Create a test Car object"""
        self.car = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2022,
            fuel_type="Petrol",
            daily_rate=Decimal("100.00"),
            inventory=5,
        )

    def test_car_serializer_fields(self):
        """Check that CarSerializer returns correct fields"""
        serializer = CarSerializer(self.car)
        data = serializer.data
        self.assertEqual(data["brand"], "Toyota")
        self.assertEqual(data["model"], "Camry")
        self.assertEqual(data["year"], 2022)
        self.assertEqual(data["fuel_type"], "Petrol")
        self.assertEqual(data["daily_rate"], "100.00")
        self.assertEqual(data["inventory"], 5)
        self.assertIn("image", data)

    def test_car_list_serializer_includes_cars_available(self):
        """Check that CarListSerializer includes cars_available field"""
        self.car.cars_available = 3
        serializer = CarListSerializer(self.car)
        data = serializer.data
        self.assertIn("cars_available", data)
        self.assertEqual(data["cars_available"], 3)

    def test_car_detail_serializer_matches_base(self):
        """Check that CarDetailSerializer matches CarSerializer fields"""
        serializer = CarDetailSerializer(self.car)
        data = serializer.data
        self.assertEqual(data["brand"], "Toyota")
        self.assertEqual(data["model"], "Camry")
        self.assertEqual(data["year"], 2022)
        self.assertEqual(data["fuel_type"], "Petrol")
        self.assertEqual(data["daily_rate"], "100.00")
        self.assertEqual(data["inventory"], 5)

    def test_car_image_serializer_only_id_and_image(self):
        """Check that CarImageSerializer returns only id and image fields"""
        serializer = CarImageSerializer(self.car)
        data = serializer.data
        self.assertIn("id", data)
        self.assertIn("image", data)
        self.assertEqual(set(data.keys()), {"id", "image"})
