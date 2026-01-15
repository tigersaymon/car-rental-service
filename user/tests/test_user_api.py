from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
ME_URL = reverse("user:manage")


class UserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Checking successful user registration"""
        payload = {"email": "test@test.com", "password": "password123"}
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_token_obtain(self):
        """Verification of receipt JWT tokens"""
        get_user_model().objects.create_user(email="test@test.com", password="password123")
        payload = {"email": "test@test.com", "password": "password123"}
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_auth_required_for_me(self):
        """Checking that access to /me/ is closed without tokens (Permissions)"""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
