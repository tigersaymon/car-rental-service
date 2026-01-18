import unittest
from unittest.mock import Mock, patch

from django.urls import reverse
from rest_framework.test import APIClient


CREATE_USER_URL = reverse("user:create")
GOOGLE_REDIRECT_URL = reverse("user:google-auth-redirect")
GOOGLE_EXCHANGE_URL = reverse("user:google_exchange_code")


class GoogleAuthViewsTests(unittest.TestCase):
    """Tests for Google OAuth2 views."""

    def setUp(self):
        """Set up API client."""
        self.client = APIClient()

    def test_google_redirect_view(self):
        """Test GET returns authorization URL."""
        res = self.client.get(GOOGLE_REDIRECT_URL)
        self.assertEqual(res.status_code, 200)
        self.assertIn("auth_url", res.data)

    @patch("user.services.google_oauth.GoogleOAuth.exchange_code_for_user_data")
    @patch("django.contrib.auth.get_user_model")
    def test_google_exchange_code_success(self, mock_get_user_model, mock_exchange):
        """Test POST exchanges code and returns JWT."""
        mock_exchange.return_value = {"email": "test@example.com", "given_name": "Test", "family_name": "User"}

        mock_user = Mock()
        mock_user.set_unusable_password = Mock()
        mock_user.save = Mock()
        mock_get_user_model().objects.get_or_create.return_value = (mock_user, True)

        payload = {"code": "dummy_code"}
        res = self.client.post(GOOGLE_EXCHANGE_URL, payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_google_exchange_code_no_code(self):
        """Test POST without code returns 400."""
        res = self.client.post(GOOGLE_EXCHANGE_URL, {}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.data)

    @patch("user.services.google_oauth.GoogleOAuth.exchange_code_for_user_data")
    def test_google_exchange_code_failure(self, mock_exchange):
        """Test POST with failing exchange returns 400."""
        mock_exchange.side_effect = ValueError({"error": "Failed"})
        payload = {"code": "dummy_code"}
        res = self.client.post(GOOGLE_EXCHANGE_URL, payload, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.data)
