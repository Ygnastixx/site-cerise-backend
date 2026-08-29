# tests.py (Mise à jour de GenerationSlidesTests)

from datetime import datetime, timezone as tz
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course, Section
from courses.schemas import SECTION_SCHEMAS
from users.models import User


class GenerationSlidesTests(BaseStudioTests):
    def setUp(self):
        super().setUp()
        self.cours = Course.objects.create(
            title="Cours Python Avance",
            description="Les decorateurs et generateurs",
            author=self.staff,
        )
        titre = Section.objects.create(
            course=self.cours,
            title="Introduction aux Decorateurs",
            type="TITLE",  # Utilisation directe du code de type
            order=1,
        )
        Section.objects.create(
            course=self.cours,
            parent=titre,
            title="Exemple de syntaxe",
            type="CODE",
            content={"code": "@my_decorator\ndef hello(): pass", "language": "python"},
            order=2,
        )

    def test_structure_des_slides(self):
        """Vérifie la génération standard de la structure des slides."""
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(reponse.data["presentation_title"], "Cours Python Avance")

        slides = reponse.data["slides"]
        self.assertEqual(len(slides), 3)  # Slide de titre globale + 2 sections

        self.assertEqual(slides[1]["slide_number"], 2)
        self.assertEqual(slides[1]["type"], "TITLE_SLIDE")
        self.assertEqual(slides[1]["title"], "Introduction aux Decorateurs")

        self.assertEqual(slides[2]["type"], "CODE_LAYOUT")
        self.assertEqual(slides[2]["title"], "Exemple de syntaxe")
        self.assertEqual(slides[2]["code_content"], "@my_decorator\ndef hello(): pass")

    def test_ajout_nouveau_type_dans_schemas_sauvegarde_et_genere_slide(self):
        """
        Vérifie qu'un nouveau type déclaré dans SECTION_SCHEMAS 
        est instantanément géré par le service sans modifier le code de services.py.
        """
        # 1. Ajout dynamique d'un nouveau type dans le dictionnaire de schéma
        SECTION_SCHEMAS['QUIZ'] = {
            'label': 'Quiz Interactif',
            'layout': 'QUIZ_LAYOUT',
            'fields': {
                'question': {'type': 'string', 'required': True}
            },
            'extractor': lambda content: {
                "question_text": content.get("question", ""),
                "total_choices": len(content.get("choices", []))
            }
        }

        # 2. Création de la section en BDD
        Section.objects.create(
            course=self.cours,
            title="Auto-évaluation",
            type="QUIZ",
            content={
                "question": "Que retourne une fonction sans return ?",
                "choices": ["None", "0", "False"]
            },
            order=3,
        )

        # 3. Appel du service de génération de slides via l'API
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        slides = reponse.data["slides"]
        
        # Vérification du 4ème slide (Index 3)
        self.assertEqual(len(slides), 4)
        self.assertEqual(slides[3]["type"], "QUIZ_LAYOUT")
        self.assertEqual(slides[3]["title"], "Auto-évaluation")
        self.assertEqual(slides[3]["question_text"], "Que retourne une fonction sans return ?")
        self.assertEqual(slides[3]["total_choices"], 3)

    def test_fallback_si_type_sans_extractor_specifique(self):
        """
        Vérifie que si un type a un layout mais pas d'extractor personnalisé,
        ses données JSON sont injectées par défaut sans faire planter le service.
        """
        SECTION_SCHEMAS['INFO'] = {
            'label': 'Note informative',
            'layout': 'INFO_LAYOUT'
            # Pas de fonction 'extractor' définie ici
        }

        Section.objects.create(
            course=self.cours,
            title="Remarque importante",
            type="INFO",
            content={"note": "Pensez à faire les exercices", "priority": "high"},
            order=3,
        )

        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        slides = reponse.data["slides"]
        
        self.assertEqual(slides[3]["type"], "INFO_LAYOUT")
        self.assertEqual(slides[3]["note"], "Pensez à faire les exercices")
        self.assertEqual(slides[3]["priority"], "high")

    def test_membre_bloque_sur_un_cours_non_publie(self):
        """Vérifie les permissions d'accès au cours non publié."""
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)

    def test_membre_autorise_si_le_cours_est_publie(self):
        """Vérifie l'accès au cours s'il est au statut PUBLISHED."""
        self.cours.status = Course.Status.PUBLISHED
        self.cours.save()
        self.client.force_authenticate(user=self.membre)

        reponse = self.client.post(
            reverse("studio:generate-slides"), {"course_id": self.cours.id}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)