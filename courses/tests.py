from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CourseAPITestCase(APITestCase):

    def setUp(self):
        """Configuration initiale exécutée avant chaque test."""
        # 1. Création d'un utilisateur de test (avec le champ matricule)
        self.user = User.objects.create_user(
            matricule="2954",
            username="testuser",
            email="test@example.com",
            password="Password123!",
            role="MEMBER",
            is_approved=True,
        )

        # 2. Génération du token JWT pour l'utilisateur
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 3. URL de l'endpoint à tester (définie dans urls.py avec name='course-list')
        self.url = reverse("course-list")

    def test_get_courses_unauthenticated_fails(self):
        """Vérifie que l'accès sans Token renvoie un code 401 Unauthorized."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_courses_authenticated_success(self):
        """Vérifie l'accès réussi (200 OK) avec un Token JWT valide dans les headers."""
        # Injecte le token Bearer dans le header Authorization du client de test
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_course_success(self):
        """Vérifie la création d'un cours (201 Created) par un utilisateur authentifié."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        payload = {
            "title": "Introduction à Django REST Framework",
            "description": "Cours de test pour l'API",
            "status": "DRAFT",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["title"], "Introduction à Django REST Framework"
        )