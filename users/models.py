from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    matricule = models.CharField(max_length=50, primary_key=True, unique=True)
    
    ROLE_CHOICES = [
        ('MEMBER', 'Membre'),
        ('STAFF', 'Staff'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    is_approved = models.BooleanField(default=False)

    USERNAME_FIELD = 'matricule'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return f"{self.matricule} - {self.username}"
    