# courses/permissions.py
from rest_framework import permissions

class CoursePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # La lecture est accessible aux utilisateurs connectés
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Seuls le Staff et les Superusers peuvent créer / modifier / supprimer
        return request.user and (request.user.is_staff or request.user.is_superuser)