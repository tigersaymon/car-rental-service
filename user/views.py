from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.serializers import UserSerializer


@extend_schema_view(
    post=extend_schema(
        description="Endpoint for registering a new user in the system.",
        responses={201: UserSerializer}
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
