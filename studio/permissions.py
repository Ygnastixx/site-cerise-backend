from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Accès réservé aux ADMIN approuvés."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return (
            bool(getattr(request.user, "is_approved", False))
            and getattr(request.user, "role", None) == "ADMIN"
        )


class IsStaffOrAdmin(BasePermission):
    """Accès réservé aux STAFF et ADMIN approuvés."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return (
            bool(getattr(request.user, "is_approved", False))
            and (
                getattr(request.user, "role", None) in {"STAFF", "ADMIN"}
                or request.user.is_staff
            )
        )