import tempfile
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from car.models import Car
from car.serializers import CarDetailSerializer
from rental.models import Rental


CAR_LIST_URL = reverse("car:car-list")


def image_upload_url(car_id: int) -> str:
    """
    Return the URL for uploading an image to a specific car.

    Args:
        car_id (int): The ID of the car.

    Returns:
        str: The generated URL.
    """
    return reverse("car:car-upload-image", args=[car_id])


def detail_url(car_id: int) -> str:
    """
    Return the URL for retrieving specific car details.

    Args:
        car_id (int): The ID of the car.

    Returns:
        str: The generated URL.
    """
    return reverse("car:car-detail", args=[car_id])


def sample_car(**params: Any) -> Car:
    """
    Create and return a sample Car instance for testing.

    Args:
        **params: Arbitrary keyword arguments to override default car attributes.

    Returns:
        Car: The created Car instance.
    """
    defaults = {
        "brand": "Toyota",
        "model": "Camry",
        "year": 2022,
        "fuel_type": "Petrol",
        "daily_rate": Decimal("100.00"),
        "inventory": 5,
    }
    defaults.update(params)
    return Car.objects.create(**defaults)


class UnauthenticatedCarApiTests(TestCase):
    """
    Test suite for unauthenticated access to Car API endpoints.
    """

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_required(self) -> None:
        """
        Test that authentication is required to access the car list.
        Expects HTTP 401 Unauthorized.
        """
        res: Response = self.client.get(CAR_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedCarApiTests(TestCase):
    """
    Test suite for authenticated (non-admin) user access to Car API.
    Verifies read access and restriction of write operations.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email="user@test.com", password="password123")
        self.client.force_authenticate(self.user)

    def test_list_cars(self) -> None:
        """
        Test retrieving a list of cars.
        Verifies that the response contains the correct number of cars
        and follows the expected serialization structure.
        """
        sample_car()
        sample_car(brand="BMW", model="X5")

        res: Response = self.client.get(CAR_LIST_URL)

        cars: QuerySet[Car] = Car.objects.all().order_by("brand")  # noqa

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 2)

    def test_retrieve_car_detail(self) -> None:
        """
        Test retrieving details for a specific car.
        Verifies the data matches the CarDetailSerializer output.
        """
        car = sample_car()
        url = detail_url(car.id)
        res: Response = self.client.get(url)

        serializer = CarDetailSerializer(car)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_car_forbidden(self) -> None:
        """
        Test that a regular user cannot create a car.
        Expects HTTP 403 Forbidden.
        """
        payload = {
            "brand": "Ford",
            "model": "Focus",
            "year": 2020,
            "daily_rate": 50,
            "inventory": 2,
        }
        res: Response = self.client.post(CAR_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_car_forbidden(self) -> None:
        """
        Test that a regular user cannot update a car.
        Expects HTTP 403 Forbidden.
        """
        car = sample_car()
        url = detail_url(car.id)
        payload = {"brand": "Updated Brand"}

        res: Response = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_car_forbidden(self) -> None:
        """
        Test that a regular user cannot delete a car.
        Expects HTTP 403 Forbidden.
        """
        car = sample_car()
        url = detail_url(car.id)

        res: Response = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_brand(self) -> None:
        """
        Test filtering cars by brand name.
        """
        car1 = sample_car(brand="Toyota")
        sample_car(brand="BMW")

        res: Response = self.client.get(CAR_LIST_URL, {"brand": "Toyota"})

        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], car1.id)

    def test_search_cars(self) -> None:
        """
        Test searching cars by brand or model.
        """
        car1 = sample_car(brand="Toyota", model="Camry")
        sample_car(brand="Honda", model="Civic")

        res: Response = self.client.get(CAR_LIST_URL, {"search": "Camry"})
        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], car1.id)

    def test_ordering_cars(self) -> None:
        """
        Test ordering cars by fields (e.g., daily_rate).
        """
        car1 = sample_car(daily_rate=Decimal("100.00"))
        car2 = sample_car(daily_rate=Decimal("50.00"))

        res: Response = self.client.get(CAR_LIST_URL, {"ordering": "daily_rate"})
        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(data[0]["id"], car2.id)

        res = self.client.get(CAR_LIST_URL, {"ordering": "-daily_rate"})
        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(data[0]["id"], car1.id)


class CarAvailabilityTests(TestCase):
    """
    Test suite for car availability logic.
    Ensures cars are correctly shown or hidden based on
    inventory and existing rental bookings.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email="user@test.com", password="password123")
        self.client.force_authenticate(self.user)

        self.car = sample_car(inventory=1)

        self.today = timezone.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.day_after = self.today + timedelta(days=2)

    def test_car_is_hidden_if_fully_booked(self) -> None:
        """
        Test that a car is NOT returned in the list if its inventory
        is fully booked for the requested dates.
        """
        Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.tomorrow,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

        params = {
            "start_date": self.tomorrow,
            "end_date": self.tomorrow,
        }
        res: Response = self.client.get(CAR_LIST_URL, params)

        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 0)

    def test_car_is_shown_if_dates_dont_overlap(self) -> None:
        """
        Test that a car IS returned if the booking dates do not overlap
        with the requested filter dates.
        """
        Rental.objects.create(
            user=self.user,
            car=self.car,
            start_date=self.tomorrow,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

        params = {"start_date": self.day_after, "end_date": self.day_after}
        res: Response = self.client.get(CAR_LIST_URL, params)

        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.car.id)

    def test_car_is_shown_if_inventory_is_sufficient(self) -> None:
        """
        Test that a car IS returned if there is still inventory available,
        even if there are existing bookings for the same dates.
        """
        car_multi = sample_car(inventory=2)

        Rental.objects.create(
            user=self.user,
            car=car_multi,
            start_date=self.tomorrow,
            end_date=self.tomorrow,
            status=Rental.Status.BOOKED,
        )

        params = {"start_date": self.tomorrow, "end_date": self.tomorrow}
        res: Response = self.client.get(CAR_LIST_URL, params)

        data = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        ids = [item["id"] for item in data]
        self.assertIn(car_multi.id, ids)


class AdminCarApiTests(TestCase):
    """
    Test suite for Admin user operations.
    Verifies that admins can create, update, delete cars and upload images.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(email="admin@test.com", password="adminpassword")
        self.client.force_authenticate(self.admin)

    def test_create_car(self) -> None:
        """
        Test that an admin can create a new car.
        Expects HTTP 201 Created.
        """
        payload = {
            "brand": "New Brand",
            "model": "Model X",
            "year": 2024,
            "fuel_type": "ELECTRIC",
            "daily_rate": "150.00",
            "inventory": 10,
        }
        res: Response = self.client.post(CAR_LIST_URL, payload)

        if res.status_code != status.HTTP_201_CREATED:
            print(res.data)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Car.objects.filter(brand="New Brand").exists())

    def test_update_car(self) -> None:
        """
        Test that an admin can update an existing car using PATCH.
        Expects HTTP 200 OK.
        """
        car = sample_car()
        url = detail_url(car.id)
        payload = {"brand": "Updated Brand"}

        res: Response = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        car.refresh_from_db()
        self.assertEqual(car.brand, "Updated Brand")

    def test_delete_car(self) -> None:
        """
        Test that an admin can delete a car.
        Expects HTTP 204 No Content.
        """
        car = sample_car()
        url = detail_url(car.id)

        res: Response = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Car.objects.filter(id=car.id).exists())

    def test_upload_image_success(self) -> None:
        """
        Test successful image upload for a car by an admin.
        Creates a temporary image file and verifies it is saved.
        """
        car = sample_car()
        url = image_upload_url(car.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            res: Response = self.client.post(url, {"image": ntf}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        car.refresh_from_db()
        self.assertTrue(car.image)
        self.assertIn("image", res.data)

        if car.image:
            car.image.delete()

    def test_upload_image_bad_request(self) -> None:
        """
        Test that uploading an invalid file (not an image) returns an error.
        Expects HTTP 400 Bad Request.
        """
        car = sample_car()
        url = image_upload_url(car.id)

        res: Response = self.client.post(url, {"image": "not-an-image"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
