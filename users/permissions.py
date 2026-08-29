from rest_framework.permissions import BasePermission

class IsBureauOrAdmin(BasePermission):
    """Autorise l'accès uniquement aux membres du Bureau ou Administrateurs."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role in ['admin', 'bureau'] or request.user.is_staff)
        )