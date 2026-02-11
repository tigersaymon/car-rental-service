from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrIfAuthenticatedReadOnly(BasePermission):
    """
    Custom permission to allow read-only access for authenticated users,
    while restricting write access (create/update/delete) to admins only.

    - Authenticated users: GET, HEAD, OPTIONS (Safe methods)
    - Admins: All methods (GET, POST, PUT, PATCH, DELETE)
    - Unauthenticated: No access
    """

    def has_permission(self, request, view):
        """
        Check global permissions for the request.
        """
        return bool(
            (request.method in SAFE_METHODS and request.user and request.user.is_authenticated)
            or (request.user and request.user.is_staff)
        )
