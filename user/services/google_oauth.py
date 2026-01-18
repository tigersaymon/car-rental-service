from urllib.parse import urlencode

import httpx
from django.conf import settings


class GoogleOAuth:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        self.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self):
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.authorization_endpoint}?{urlencode(params)}"

    async def get_user_data(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
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
            token_resp.raise_for_status()
            token = token_resp.json()

            user_resp = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {token['access_token']}"},
            )
            user_resp.raise_for_status()
            return user_resp.json()


google_oauth = GoogleOAuth()
