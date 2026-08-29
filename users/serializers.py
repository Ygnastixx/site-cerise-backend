from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['matricule', 'username', 'email', 'role', 'is_approved', 'is_active']

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['matricule', 'username', 'email', 'password', 'role', 'is_approved']
        read_only_fields = ['is_approved']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, is_approved=False)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD  # Utilise le champ d'identifiant configuré sur le modèle User

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_approved:
            raise PermissionDenied("Votre compte n'a pas encore été approuvé par un administrateur.")
        
        data['role'] = getattr(self.user, 'role', 'MEMBER')
        data['matricule'] = self.user.matricule
        return data

class ApproveUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_approved']