# courses/tests.py
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Course, Section

User = get_user_model()


class CourseAPITestCase(APITestCase):
    def setUp(self):
        # 1. Utilisateur STAFF approuvé (accès complet en écriture)
        self.user1 = User.objects.create_user(
            matricule="2954",
            username="dev1",
            password="Password123!",
            is_approved=True,
            role="STAFF",      # ou is_staff=True selon ton champ User
            is_staff=True
        )

        # 2. Autre utilisateur STAFF approuvé
        self.user2 = User.objects.create_user(
            matricule="3000",
            username="dev2",
            password="Password123!",
            is_approved=True,
            role="STAFF",
            is_staff=True
        )

        # 3. Membre normal non-staff mais approuvé (pour tester les restrictions d'écriture)
        self.normal_member = User.objects.create_user(
            matricule="4000",
            username="member1",
            password="Password123!",
            is_approved=True,
            role="MEMBER"
        )

        # Configuration du client API avec authentification JWT
        self.client = APIClient()
        self.token_user1 = str(RefreshToken.for_user(self.user1).access_token)
        self.token_user2 = str(RefreshToken.for_user(self.user2).access_token)
        self.token_normal_member = str(RefreshToken.for_user(self.normal_member).access_token)

        # Jeux de données pour les tests
        self.course_user1 = Course.objects.create(
            title="Introduction à Python",
            description="Bases de la programmation orientée objet",
            status=Course.Status.PUBLISHED,
            is_template=False,
            author=self.user1
        )
        self.course_user2 = Course.objects.create(
            title="Bases de données Oracle",
            description="Administration et SQL avancé",
            status=Course.Status.DRAFT,
            is_template=True,
            author=self.user2
        )

        # Endpoints
        self.courses_url = reverse("course-list")
        self.sections_url = reverse("section-list")
        self.schemas_url = reverse("section-schemas")


    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # ==========================================
    # 1. TESTS DES PERMISSIONS ET JWT
    # ==========================================

    def test_unauthenticated_user_cannot_access_courses(self):
        """Un utilisateur anonyme ne peut pas lire ni modifier les cours."""
        self.client.credentials()  # Retrait des tokens
        response = self.client.get(self.courses_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_authenticated_user_can_list_courses(self):
        """Un utilisateur authentifié via JWT peut récupérer la liste des cours."""
        self.authenticate(self.token_user1)
        response = self.client.get(self.courses_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_course_creation_assigns_authenticated_user_as_author(self):
        """La création d'un cours assigne automatiquement request.user comme auteur."""
        self.authenticate(self.token_user1)
        payload = {
            "title": "Nouveau cours Django",
            "description": "API REST avec DRF",
            "status": Course.Status.DRAFT
        }
        response = self.client.post(self.courses_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author_matricule"], self.user1.matricule)

    # ==========================================
    # 2. TESTS DES FILTRES DE RECHERCHE
    # ==========================================

    def test_filter_courses_by_status(self):
        """Test du filtre par statut (DRAFT, PUBLISHED)."""
        self.authenticate(self.token_user1)
        response = self.client.get(self.courses_url, {"status": "PUBLISHED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Introduction à Python")

    def test_filter_courses_by_is_template(self):
        """Test du filtre sur les modèles (is_template=true/false)."""
        self.authenticate(self.token_user1)
        response = self.client.get(self.courses_url, {"is_template": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Bases de données Oracle")

    def test_filter_courses_by_author_matricule(self):
        """Test du filtre par matricule d'auteur."""
        self.authenticate(self.token_user1)
        response = self.client.get(self.courses_url, {"author": self.user2.matricule})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["author_matricule"], self.user2.matricule)

    def test_search_courses_by_query_string(self):
        """Test du filtre de recherche textuelle 'search' / 'q' (sur titre ou description)."""
        self.authenticate(self.token_user1)
        response = self.client.get(self.courses_url, {"search": "orientée objet"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Introduction à Python")

    # ==========================================
    # 3. TESTS DES ACTIONS PERSO & ARBORESCENCE
    # ==========================================

    def test_course_duplication(self):
        """Test de la duplication d'un cours et de la reconstruction de ses sections."""
        self.authenticate(self.token_user1)
        sec_root = Section.objects.create(
            course=self.course_user1, title="Chapitre 1", type="TITLE", order=1
        )
        Section.objects.create(
            course=self.course_user1, parent=sec_root, title="Leçon 1.1", type="TEXT", content={"text": "Hello"}, order=2
        )

        url = reverse("course-duplicate", kwargs={"pk": self.course_user1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("(copie)", response.data["title"])
        
        # 1 section racine ("Chapitre 1")
        self.assertEqual(len(response.data["sections"]), 1)
        # 1 sous-section enfant ("Leçon 1.1") imbriquée dans la racine
        self.assertEqual(len(response.data["sections"][0]["children"]), 1)
        self.assertEqual(response.data["sections"][0]["children"][0]["title"], "Leçon 1.1")

    def test_section_schemas_endpoint(self):
        """Vérifie que l'endpoint des schémas retourne la configuration des widgets pour le frontend."""
        self.authenticate(self.token_user1)
        response = self.client.get(self.schemas_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("TEXT", response.data)
        self.assertIn("CODE", response.data)

    def test_section_schema_validation_error(self):
        """Vérifie qu'une erreur de validation est levée si un champ JSON obligatoire est manquant."""
        self.authenticate(self.token_user1)
        payload = {
            "course": self.course_user1.id,
            "title": "Extrait Python",
            "type": "CODE",
            "content": {"language": "python"}  # Manque le champ obligatoire 'code'
        }
        response = self.client.post(self.sections_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)

    def test_section_reorder_action(self):
        """Test du réordonnancement par lot (bulk reorder)."""
        self.authenticate(self.token_user1)
        sec1 = Section.objects.create(course=self.course_user1, title="Section 1", type="TEXT", order=1)
        sec2 = Section.objects.create(course=self.course_user1, title="Section 2", type="TEXT", order=2)

        url = reverse("section-reorder")
        payload = {
            "items": [
                {"id": sec1.id, "order": 10},
                {"id": sec2.id, "order": 5}
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sec1.refresh_from_db()
        sec2.refresh_from_db()
        self.assertEqual(sec1.order, 10)
        self.assertEqual(sec2.order, 5)

    def test_normal_member_cannot_create_course(self):
        """Un membre normal approuvé (non STAFF/ADMIN) ne peut pas créer de cours."""
        self.authenticate(self.token_normal_member)
        payload = {
            "title": "Tentative de cours",
            "description": "Test",
            "status": Course.Status.DRAFT
        }
        response = self.client.post(self.courses_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
