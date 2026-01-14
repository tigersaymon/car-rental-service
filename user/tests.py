from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
ME_URL = reverse("user:manage")


class UserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_create_user_success(self):
        """Successful user registration test"""
        res = self.client.post(USER_URL, self.user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password"]))

    def test_token_obtain(self):
        """JWT token acquisition test"""
        get_user_model().objects.create_user(**self.user_data)
        res = self.client.post(TOKEN_URL, {"email": self.user_data["email"], "password": self.user_data["password"]})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_auth_required_for_me(self):
        """Checking that access to /me/ without a token is prohibited"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
