from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Accès réservé aux ADMIN approuvés.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return (
            user.is_approved
            and user.role == "ADMIN"
        )

class IsStaffOrAdmin(BasePermission): 
    """ Accès réservé aux STAFF et ADMIN approuvés. """ 

    def has_permission(self, request, view): 
        user = request.user 
        if not user or not user.is_authenticated: 
            return False 
        if user.is_superuser: 
            return True 
        return ( user.is_approved and user.role in {"STAFF", "ADMIN"} )