import os
import uuid
from decimal import Decimal

from django.test import TestCase

from car.models import Car, car_image_file_path


class CarModelTests(TestCase):
    """Tests for Car model"""

    def setUp(self):
        """Create a test Car object"""
        self.car = Car.objects.create(
            brand="Toyota",
            model="Corolla",
            year=2020,
            fuel_type=Car.FuelType.GAS,
            daily_rate=Decimal("50.00"),
            inventory=3,
        )

    def test_str_representation(self):
        """Check string representation of Car"""
        expected = "Toyota Corolla (2020)"
        self.assertEqual(str(self.car), expected)

    def test_meta_ordering(self):
        """Check ordering by brand and model"""
        Car.objects.create(
            brand="Audi",
            model="A4",
            year=2021,
            fuel_type=Car.FuelType.DIESEL,
            daily_rate=Decimal("70.00"),
            inventory=2,
        )
        cars = Car.objects.all()
        self.assertEqual(list(cars), sorted(cars, key=lambda c: (c.brand, c.model)))

    def test_car_image_file_path(self):
        """Check generated upload path for car image"""
        filename = "myimage.jpg"
        path = car_image_file_path(self.car, filename)

        self.assertTrue(path.startswith("uploads/cars/"))
        self.assertTrue(path.endswith(".jpg"))
        self.assertIn("toyota-", path)

        generated_filename = os.path.basename(path)
        uuid_str = generated_filename.replace("toyota-", "").replace(".jpg", "")
        uuid_obj = uuid.UUID(uuid_str)
        self.assertIsInstance(uuid_obj, uuid.UUID)
