from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_approved', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    matricule = models.CharField(max_length=50, primary_key=True, unique=True)

    ROLE_CHOICES = [
        ('MEMBER', 'Membre'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    is_approved = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'matricule'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return f"{self.matricule} - {self.username}"