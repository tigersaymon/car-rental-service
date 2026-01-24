from urllib.parse import unquote, urlencode

import httpx
from django.conf import settings


class GoogleOAuth:
    """
    Service class for handling Google OAuth2 flow.
    """

    def __init__(self):
        """
        Initializes the GoogleOAuth instance with client credentials
        and endpoints for authorization, token exchange, and user info.
        """
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        self.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self) -> str:
        """
        Generates the Google OAuth2 authorization URL.

        Returns:
            str: The URL to redirect the user to for Google login consent.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.authorization_endpoint}?{urlencode(params)}"

    def exchange_code_for_user_data(self, code: str) -> dict:
        """
        Exchanges an authorization code for an access token and retrieves
        the user's profile data from Google.

        Args:
            code (str): The authorization code received from the Google callback.

        Returns:
            dict: A dictionary containing user info (email, name, picture, etc.).

        Raises:
            ValueError: If the token exchange fails or user data cannot be retrieved.
        """
        code = unquote(code)

        token_resp = httpx.post(
            self.token_endpoint,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code != 200:
            raise ValueError({"error": "Failed to obtain token", "details": token_resp.json()})

        access_token = token_resp.json().get("access_token")

        user_resp = httpx.get(
            self.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_resp.status_code != 200:
            raise ValueError({"error": "Failed to obtain user data"})

        return user_resp.json()


google_oauth = GoogleOAuth()
