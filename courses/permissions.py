from rest_framework.permissions import BasePermission


class CoursePermission(BasePermission):
    """Lecture pour les utilisateurs authentifiés; écriture pour STAFF/ADMIN approuvés."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.user.is_superuser:
            return True
        return bool(getattr(request.user, "is_approved", False)) and (
            getattr(request.user, "role", None) in {"STAFF", "ADMIN"} or request.user.is_staff
        )