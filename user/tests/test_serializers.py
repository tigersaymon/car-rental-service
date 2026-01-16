from django.contrib.auth import get_user_model
from django.test import TestCase

from user.serializers import UserSerializer


class SerializerTests(TestCase):
    def test_user_serializer_contains_expected_fields(self):
        """Test that the serializer returns correct fields and hides the password"""
        user = get_user_model().objects.create_user(email="test@example.com", password="testpassword123")
        serializer = UserSerializer(instance=user)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "email", "first_name", "last_name", "is_staff"})
        self.assertNotIn("password", data)

    def test_user_serializer_validation(self):
        """Test that the password must be at least 5 characters"""
        payload = {"email": "test@example.com", "password": "123"}
        serializer = UserSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
