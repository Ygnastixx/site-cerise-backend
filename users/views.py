from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .permissions import IsAdmin
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegisterSerializer,
    UserSerializer,
    ApproveUserSerializer,
    ChangeRoleSerializer,
)

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

class PendingUsersListView(generics.ListAPIView):
    """GET /api/users/pending/ - Réservé aux Administrateurs."""
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(is_approved=False)

class ApproveUserView(generics.UpdateAPIView):
    """PATCH /api/users/<id>/approve/ - Réservé aux Administrateurs."""
    permission_classes = [IsAdmin]
    serializer_class = ApproveUserSerializer
    queryset = User.objects.all()
    http_method_names = ['patch']

class ChangeRoleView(generics.UpdateAPIView):
    """PATCH /api/users/<id>/role/ - Change le rôle d'un membre. Réservé aux Administrateurs."""
    permission_classes = [IsAdmin]
    serializer_class = ChangeRoleSerializer
    queryset = User.objects.all()
    http_method_names = ['patch']