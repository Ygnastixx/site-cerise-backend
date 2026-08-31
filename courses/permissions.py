```python
from rest_framework import permissions


class CoursePermission(permissions.BasePermission):
    """
    Lecture des cours : utilisateurs authentifiés et approuvés.

    Création / modification / suppression :
    STAFF et ADMIN uniquement.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Lecture
        if request.method in permissions.SAFE_METHODS:
            return user.is_approved or user.is_superuser

        # Écriture
        if user.is_superuser:
            return True

        return (
            user.is_approved
            and user.role in {"STAFF", "ADMIN"}
        )
```
