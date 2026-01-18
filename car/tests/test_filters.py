from decimal import Decimal

from django.db import models
from django.db.models import F, IntegerField, Value
from django.test import RequestFactory, TestCase

from car.filters import CarFilter
from car.models import Car


class CarFilterTest(TestCase):
    """
    Test suite for CarFilter.
    Tests standard filtering fields and custom methods for availability and dates.
    """

    def setUp(self) -> None:
        self.factory = RequestFactory()

        self.car_available = Car.objects.create(
            brand="Toyota",
            model="Camry",
            year=2015,
            daily_rate=Decimal("50.00"),
            fuel_type="Petrol",
            inventory=1,
        )

        self.car_unavailable = Car.objects.create(
            brand="BMW",
            model="X5",
            year=2022,
            daily_rate=Decimal("150.00"),
            fuel_type="Diesel",
            inventory=0,
        )

        self.car_honda = Car.objects.create(
            brand="Honda",
            model="Civic",
            year=2019,
            daily_rate=Decimal("80.00"),
            fuel_type="Petrol",
            inventory=2,
        )

    def test_filter_by_brand(self) -> None:
        """Test filtering by brand (icontains)."""
        data = {"brand": "toyota"}
        filter_set = CarFilter(data=data, queryset=Car.objects.all())

        self.assertTrue(filter_set.is_valid())
        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), self.car_available)

    def test_filter_by_price_range(self) -> None:
        """Test filtering by min and max price."""
        data = {"price_min": 60, "price_max": 100}
        filter_set = CarFilter(data=data, queryset=Car.objects.all())

        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), self.car_honda)

    def test_filter_by_year_range(self) -> None:
        """Test filtering by min and max year."""
        data = {"min_year": 2018}
        filter_set = CarFilter(data=data, queryset=Car.objects.all())

        self.assertEqual(filter_set.qs.count(), 2)
        self.assertNotIn(self.car_available, filter_set.qs)

    def test_filter_do_nothing_dates(self) -> None:
        """
        Test that start_date and end_date params do not filter the queryset
        inside the FilterSet class (logic is handled in ViewSet).
        """
        data = {"start_date": "2024-01-01", "end_date": "2024-01-05"}
        qs = Car.objects.all()
        filter_set = CarFilter(data=data, queryset=qs)

        self.assertEqual(filter_set.qs.count(), 3)

    def test_filter_available_simple_inventory(self) -> None:
        """
        Test 'available=True' logic when NO annotation is present.
        Should simply check inventory > 0.
        """
        data = {"available": "true"}
        filter_set = CarFilter(data=data, queryset=Car.objects.all())

        self.assertEqual(filter_set.qs.count(), 2)
        self.assertNotIn(self.car_unavailable, filter_set.qs)

        data_false = {"available": "false"}
        filter_set_false = CarFilter(data=data_false, queryset=Car.objects.all())

        self.assertEqual(filter_set_false.qs.count(), 1)
        self.assertEqual(filter_set_false.qs.first(), self.car_unavailable)

    def test_filter_available_with_annotation(self) -> None:
        """
        Test 'available=True' logic when 'cars_available' annotation IS present.
        This simulates the ViewSet logic where inventory is dynamically calculated.
        """
        qs = Car.objects.annotate(
            cars_available=models.Case(
                models.When(brand="Honda", then=Value(0)),
                default=F("inventory"),
                output_field=IntegerField(),
            )
        )

        honda = qs.get(brand="Honda")
        self.assertEqual(honda.cars_available, 0)

        data = {"available": "true"}
        filter_set = CarFilter(data=data, queryset=qs)

        self.assertEqual(filter_set.qs.count(), 1)
        self.assertEqual(filter_set.qs.first(), self.car_available)
