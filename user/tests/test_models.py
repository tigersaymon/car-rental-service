from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    def test_user_str(self):
        """Tests the string representation of the User model."""
        email = "test@example.com"
        user = get_user_model().objects.create_user(email=email, password="testpassword123")
        self.assertEqual(str(user), email)

    def test_create_user_with_email_successful(self):
        """Tests successful user creation via UserManager."""
        email = "admin@example.com"
        password = "testpassword123"
        user = get_user_model().objects.create_user(email=email, password=password)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_superuser(self):
        """Tests creating a superuser via CLI/Manager."""
        user = get_user_model().objects.create_superuser(email="admin@test.com", password="adminpassword")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_new_user_invalid_email(self):
        """Tests that creating a user with no email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "password123")

    def test_password_is_hashed(self):
        """Tests that the password is hashed upon creation."""
        password = "secret_password"
        user = get_user_model().objects.create_user(email="hash@test.com", password=password)
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))
