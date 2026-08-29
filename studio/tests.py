from datetime import datetime, timezone as tz

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course, Section
from inventory.models import Equipment
from sessions_app.models import Session, SessionEquipment
from users.models import User

from .models import SlideTemplate


class BaseStudioTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "chef", "chef@example.com", "motdepassesecurise",
            matricule=1, role="ADMIN", is_approved=True,
        )
        self.staff = User.objects.create_user(
            "staff", "staff@example.com", "motdepassesecurise",
            matricule=2, role="STAFF", is_approved=True,
        )
        self.membre = User.objects.create_user(
            "membre", "membre@example.com", "motdepassesecurise",
            matricule=3, role="MEMBER", is_approved=True,
        )


class TemplateTests(BaseStudioTests):
    def test_seul_ladmin_peut_televerser_un_gabarit(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:template-list"),
            {"name": "Affiche cerise", "layout_type": "POSTER", "template_file": "poster_a.svg"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_creation_par_ladmin(self):
        self.client.force_authenticate(user=self.admin)
        reponse = self.client.post(
            reverse("studio:template-list"),
            {"name": "Affiche cerise", "layout_type": "POSTER", "template_file": "poster_a.svg"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reponse.data["created_by_matricule"], self.admin.matricule)

    def test_galerie_consultable_par_un_membre(self):
        SlideTemplate.objects.create(name="Gabarit", layout_type="SLIDE")
        self.client.force_authenticate(user=self.membre)

        reponse = self.client.get(reverse("studio:template-list"))

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reponse.data), 1)


class GenerationSlidesTests(BaseStudioTests):
    def setUp(self):
        super().setUp()
        self.cours = Course.objects.create(
            title="Cours Python Avance",
            description="Les decorateurs et generateurs",
            author=self.staff,
        )
        titre = Section.objects.create(
            course=self.cours, title="Introduction aux Decorateurs",
            type=Section.Type.TITLE, order=1,
        )
        Section.objects.create(
            course=self.cours, parent=titre, title="Exemple de syntaxe",
            type=Section.Type.CODE,
            content={"code": "@my_decorator\ndef hello(): pass", "language": "python"},
            order=2,
        )

    def test_structure_des_slides(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["presentation_title"], "Cours Python Avance")

        slides = reponse.data["slides"]
        self.assertEqual(len(slides), 3)  # ouverture + 2 sections

        self.assertEqual(slides[1]["slide_number"], 2)
        self.assertEqual(slides[1]["type"], "TITLE_SLIDE")
        self.assertEqual(slides[1]["title"], "Introduction aux Decorateurs")

        self.assertEqual(slides[2]["type"], "CODE_LAYOUT")
        self.assertEqual(slides[2]["title"], "Exemple de syntaxe")
        self.assertEqual(slides[2]["code_content"], "@my_decorator\ndef hello(): pass")

    def test_membre_bloque_sur_un_cours_non_publie(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_membre_autorise_si_le_cours_est_publie(self):
        self.cours.status = Course.Status.PUBLISHED
        self.cours.save()
        self.client.force_authenticate(user=self.membre)

        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)


class GenerationAfficheTests(BaseStudioTests):
    def setUp(self):
        super().setUp()
        self.seance = Session.objects.create(
            date=datetime(2026, 10, 15, 11, 0, tzinfo=tz.utc),
            location="Salle de TP 3",
            theme="Atelier Microcontroleurs ESP32",
        )
        cartes = Equipment.objects.create(
            name="Cartes ESP32", quantity=20, brand="Espressif", model="ESP32-DEVKIT",
            purchase_price=15.50, description="Cartes de développement ESP32"
        )
        cables = Equipment.objects.create(
            name="Cables Micro-USB", quantity=30, brand="Generic", model="Standard",
            purchase_price=2.00, description="Câbles de connexion micro-USB"
        )
        SessionEquipment.objects.create(session=self.seance, equipment=cartes, quantity_reserved=5)
        SessionEquipment.objects.create(session=self.seance, equipment=cables, quantity_reserved=10)

    def test_donnees_daffiche(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-poster"), {"session_id": self.seance.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["title"], "Atelier Microcontroleurs ESP32")
        self.assertEqual(reponse.data["location"], "Salle de TP 3")
        self.assertEqual(
            reponse.data["materials_needed"], ["Cartes ESP32", "Cables Micro-USB"]
        )
        # La date est rendue en toutes lettres pour le composant d'affiche.
        # Peut être en français ou anglais selon la locale Django
        self.assertIn("15", reponse.data["date_formatted"])
        self.assertIn("October", reponse.data["date_formatted"].replace("Octobre", "October").replace("octobre", "October"))

    def test_gabarit_joint_a_la_reponse(self):
        gabarit = SlideTemplate.objects.create(name="Affiche cerise", layout_type="POSTER")
        self.client.force_authenticate(user=self.staff)

        reponse = self.client.post(
            reverse("studio:generate-poster"),
            {"session_id": self.seance.id, "template_id": gabarit.id},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["template"]["name"], "Affiche cerise")

    def test_seance_inexistante(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-poster"), {"session_id": 9999}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        # L'erreur vient de la validation du PrimaryKeyRelatedField
        self.assertIn("session_id", reponse.data)


@override_settings(ANTHROPIC_API_KEY="")
class GenerationPostSocialTests(BaseStudioTests):
    """Sans cle API, l'endpoint doit produire un brouillon local exploitable."""

    def setUp(self):
        super().setUp()
        self.seance = Session.objects.create(
            date=datetime(2026, 10, 15, 11, 0, tzinfo=tz.utc),
            location="Salle 004",
            theme="Atelier ESP32",
            description="Decouverte des microcontroleurs",
        )

    def test_repli_local_sans_cle_api(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-social-post"), {"session_id": self.seance.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["source"], "fallback")
        self.assertIn("Atelier ESP32", reponse.data["generated_text"])
        self.assertIn("Salle 004", reponse.data["generated_text"])

    def test_endpoint_ferme_aux_membres(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.post(
            reverse("studio:generate-social-post"), {"session_id": self.seance.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)
