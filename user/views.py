from urllib.parse import unquote

import httpx
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers import UserSerializer
from user.services.google_oauth import google_oauth


User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        description="Endpoint for registering a new user in the system.", responses={201: UserSerializer}
    )
)
class CreateUserView(generics.CreateAPIView):
    """Register a new user (POST: users/)"""

    serializer_class = UserSerializer


@extend_schema_view(
    get=extend_schema(description="Get the profile information of the currently authenticated user."),
    put=extend_schema(description="Full update of the current user's profile."),
    patch=extend_schema(description="Partial update of the current user's profile."),
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    """Current user profile management (GET/PUT/PATCH: users/me/)"""

    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """Returns the currently authenticated user"""
        return self.request.user


@extend_schema(
    description="Get the Google OAuth2 authorization URL. Use this URL to redirect the user to Google login.",
    responses={
        200: OpenApiResponse(
            response={"auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=..."}
        )
    },
)
class GoogleAuthRedirectView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"auth_url": google_oauth.get_authorization_url()})


@extend_schema(
    description="Exchange a Google OAuth2 code for an access token and create/login a user in the system.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Authorization code received from Google after user login"}
            },
            "required": ["code"],
        }
    },
    responses={
        200: OpenApiResponse(
            response={"access": "jwt_access_token_string", "refresh": "jwt_refresh_token_string"},
            description="JWT access and refresh tokens for the authenticated user",
        ),
        400: OpenApiResponse(
            response={"error": "NO code provided or Cant receive response"},
            description="Error if code is missing or token exchange failed",
        ),
    },
    examples=[
        OpenApiExample(
            "Success Example",
            summary="Successful token exchange",
            value={
                "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            },
            response_only=True,
        ),
        OpenApiExample(
            "Error Example", summary="Missing code", value={"error": "NO code provided"}, response_only=True
        ),
    ],
)
class GoogleAuthExchangeCodeView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        code = request.data.get("code")

        if not code:
            return Response({"error": "NO code provided"}, status=status.HTTP_400_BAD_REQUEST)

        code = unquote(code)

        token_response = httpx.post(
            google_oauth.token_endpoint,
            data={
                "client_id": google_oauth.client_id,
                "client_secret": google_oauth.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": google_oauth.redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        token_data = token_response.json()

        if token_response.status_code != 200:
            return Response(
                {"error": "Cant receive response", "details": token_data}, status=status.HTTP_400_BAD_REQUEST
            )

        access_token = token_data.get("access_token")

        user_info_response = httpx.get(
            google_oauth.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_info_response.status_code != 200:
            return Response({"error": "Cant receive user data"}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()

        email = user_info.get("email")
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
            },
        )

        if created:
            user.set_unusable_password()
            user.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )
