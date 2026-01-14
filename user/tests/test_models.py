from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    def test_user_str(self):
        """Test the __str__ method of the User model"""
        email = "test@example.com"
        user = get_user_model().objects.create_user(email=email, password="testpassword123")
        self.assertEqual(str(user), email)

    def test_create_user_with_email_successful(self):
        """User creation test via UserManager"""
        email = "admin@example.com"
        password = "testpassword123"
        user = get_user_model().objects.create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_superuser(self):
        """Test creating a superuser via CLI/Manager"""
        user = get_user_model().objects.create_superuser(email="admin@test.com", password="adminpassword")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
