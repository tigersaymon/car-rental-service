from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from rest_framework.permissions import SAFE_METHODS

from car.permissions import IsAdminOrIfAuthenticatedReadOnly


class IsAdminOrIfAuthenticatedReadOnlyTests(TestCase):
    """Tests for IsAdminOrIfAuthenticatedReadOnly permission logic."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAdminOrIfAuthenticatedReadOnly()
        self.user_model = get_user_model()

    def test_unauthenticated_user_denied(self):
        """Tests that unauthenticated users are denied access entirely."""
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))

    def test_authenticated_user_safe_methods_allowed(self):
        """Tests that authenticated users can access SAFE_METHODS (GET, etc.)."""
        user = self.user_model.objects.create_user(email="user@test.com", password="pass123")
        for method in SAFE_METHODS:
            request = getattr(self.factory, method.lower())("/")
            request.user = user
            self.assertTrue(self.permission.has_permission(request, None))

    def test_authenticated_user_write_methods_denied(self):
        """Tests that authenticated (non-admin) users cannot perform write operations."""
        user = self.user_model.objects.create_user(email="user2@test.com", password="pass123")
        request = self.factory.post("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_admin_user_full_access(self):
        """Tests that admins have full access (both read and write)."""
        admin = self.user_model.objects.create_superuser(email="admin@test.com", password="adminpass")

        request_get = self.factory.get("/")
        request_get.user = admin
        self.assertTrue(self.permission.has_permission(request_get, None))

        request_post = self.factory.post("/")
        request_post.user = admin
        self.assertTrue(self.permission.has_permission(request_post, None))
