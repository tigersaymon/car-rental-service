from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Register a new user (POST: users/)"""

    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Current user profile management (GET/PUT/PATCH: users/me/)"""

    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """Returns the currently authenticated user"""
        return self.request.user
