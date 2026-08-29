from rest_framework.permissions import BasePermission, SAFE_METHODS

class SessionPermission(BasePermission):
    """
    Lecture pour tous les membres approuvés ;
    Écriture réservée aux STAFF et ADMIN approuvés.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Vérification qu'il s'agit d'un membre approuvé
        is_approved = bool(getattr(request.user, "is_approved", False))
        if not is_approved and not request.user.is_superuser:
            return False

        # Lecture autorisée pour tout membre approuvé
        if request.method in SAFE_METHODS:
            return True

        # Écriture réservée aux ADMIN / STAFF
        if request.user.is_superuser:
            return True
            
        return getattr(request.user, "role", None) in {"STAFF", "ADMIN"} or request.user.is_staff


class IsStaffOrAdminOrReadOnly(BasePermission):
    """
    Lecture pour tous les utilisateurs authentifiés ;
    Écriture réservée aux STAFF et ADMIN.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lecture autorisée pour tout utilisateur authentifié
        if request.method in SAFE_METHODS:
            return True

        # Écriture réservée aux ADMIN / STAFF
        if request.user.is_superuser:
            return True
            
        return getattr(request.user, "role", None) in {"STAFF", "ADMIN"} or request.user.is_staff


class IsStaffOrAdmin(BasePermission):
    """
    Accès réservé aux utilisateurs STAFF et ADMIN.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
            
        return getattr(request.user, "role", None) in {"STAFF", "ADMIN"} or request.user.is_staff