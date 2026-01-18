from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrIfAuthenticatedReadOnly(BasePermission):
    """
    Custom permission for Car API.

    - Authenticated users: allowed to perform safe (read-only) methods.
    - Staff users: allowed full access, including write operations.
    """

    def has_permission(self, request, view):
        """
        Grant permission based on request method and user role.
        """
        return bool(
            (request.method in SAFE_METHODS and request.user and request.user.is_authenticated)
            or (request.user and request.user.is_staff)
        )
