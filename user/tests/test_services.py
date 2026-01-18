import unittest
from unittest.mock import Mock, patch

from user.services.google_oauth import GoogleOAuth


class TestGoogleOAuth(unittest.TestCase):
    """Unit tests for the GoogleOAuth class."""

    def setUp(self):
        """Set up a GoogleOAuth instance and dummy code for tests."""
        self.google = GoogleOAuth()
        self.dummy_code = "dummy_code"

    def test_get_authorization_url(self):
        """Test that the authorization URL is correctly generated."""
        url = self.google.get_authorization_url()
        self.assertTrue(url.startswith("https://accounts.google.com/o/oauth2/v2/auth"))
        self.assertIn(f"client_id={self.google.client_id}", url)
        self.assertIn("redirect_uri=", url)
        self.assertIn("response_type=code", url)
        self.assertIn("scope=openid+email+profile", url)

    @patch("user.services.google_oauth.httpx.get")
    @patch("user.services.google_oauth.httpx.post")
    def test_exchange_code_for_user_data_success(self, mock_post, mock_get):
        """Test successful exchange of code for user data."""
        mock_post.return_value = Mock(status_code=200, json=lambda: {"access_token": "fake_token"})
        mock_get.return_value = Mock(
            status_code=200, json=lambda: {"email": "test@example.com", "given_name": "Test", "family_name": "User"}
        )

        user_info = self.google.exchange_code_for_user_data(self.dummy_code)

        self.assertEqual(user_info["email"], "test@example.com")
        self.assertEqual(user_info["given_name"], "Test")
        self.assertEqual(user_info["family_name"], "User")

    @patch("user.services.google_oauth.httpx.post")
    def test_exchange_code_for_user_data_token_failure(self, mock_post):
        """Test that a failed token exchange raises ValueError."""
        mock_post.return_value = Mock(status_code=400, json=lambda: {"error": "invalid_grant"})
        with self.assertRaises(ValueError) as context:
            self.google.exchange_code_for_user_data(self.dummy_code)
        self.assertIn("Failed to obtain token", str(context.exception))

    @patch("user.services.google_oauth.httpx.get")
    @patch("user.services.google_oauth.httpx.post")
    def test_exchange_code_for_user_data_userinfo_failure(self, mock_post, mock_get):
        """Test that a failed user info request raises ValueError."""
        mock_post.return_value = Mock(status_code=200, json=lambda: {"access_token": "fake_token"})
        mock_get.return_value = Mock(status_code=400, json=lambda: {"error": "bad_request"})

        with self.assertRaises(ValueError) as context:
            self.google.exchange_code_for_user_data(self.dummy_code)
        self.assertIn("Failed to obtain user data", str(context.exception))
