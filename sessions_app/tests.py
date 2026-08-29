from datetime import datetime, timezone as tz

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from courses.models import Course
from inventory.models import Equipment
from users.models import User

from .models import Session


class BaseSeanceTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            "staff", "staff@example.com", "motdepassesecurise",
            matricule=1, role="STAFF", is_approved=True,
        )
        self.membre = User.objects.create_user(
            "membre", "membre@example.com", "motdepassesecurise",
            matricule=2, role="MEMBER", is_approved=True,
        )
        self.cartes = Equipment.objects.create(
            name="Cartes ESP32", quantity=20, brand="Espressif", model="ESP32-DEVKIT", 
            purchase_price=15.50, description="Cartes de développement ESP32"
        )
        self.cables = Equipment.objects.create(
            name="Cables Micro-USB", quantity=30, brand="Generic", model="Standard",
            purchase_price=2.00, description="Câbles de connexion micro-USB"
        )
        self.cours = Course.objects.create(title="Initiation Arduino", author=self.staff)


class CreationSeanceTests(BaseSeanceTests):
    def test_creation_avec_reservation_de_materiel(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("sessions_app:list-create"),
            {
                "date": "2026-10-15T14:00:00Z",
                "location": "salle 004",
                "theme": "Initiation Arduino",
                "description": "Decouverte des bases du cablage",
                "course_id": self.cours.id,
                "equipments": [
                    {"equipment_id": self.cartes.id, "quantity_reserved": 5},
                    {"equipment_id": self.cables.id, "quantity_reserved": 10},
                ],
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(reponse.data["equipments"]), 2)

        seance = Session.objects.get(id=reponse.data["id"])
        self.assertEqual(seance.equipment_reservations.count(), 2)
        self.assertEqual(seance.course_id, self.cours.id)

    def test_reservation_superieure_au_stock_refusee(self):
        self.client.force_authenticate(user=self.staff)
        reponse = self.client.post(
            reverse("sessions_app:list-create"),
            {
                "date": "2026-10-15T14:00:00Z",
                "location": "salle 004",
                "theme": "Test",
                "equipments": [{"equipment_id": self.cartes.id, "quantity_reserved": 999}],
            },
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST)
        # Erreur de validation au niveau du champ 'equipments'
        self.assertIn("Stock insuffisant", str(reponse.data.get("equipments", [])))
        self.assertEqual(Session.objects.count(), 0)

    def test_un_membre_ne_peut_pas_creer_de_seance(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.post(
            reverse("sessions_app:list-create"),
            {"date": "2026-10-15T14:00:00Z", "location": "x", "theme": "y"},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_403_FORBIDDEN)


class FiltresSeanceTests(BaseSeanceTests):
    def setUp(self):
        super().setUp()
        self.ancienne = Session.objects.create(
            date=datetime(2026, 10, 10, 14, 0, tzinfo=tz.utc),
            location="salle 1", theme="Robotique avancee",
        )
        self.recente = Session.objects.create(
            date=datetime(2026, 10, 20, 14, 0, tzinfo=tz.utc),
            location="salle 2", theme="Soudure",
        )

    def test_filtre_before_date(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.get(reverse("sessions_app:list-create"), {"before_date": "2026-10-15"})

        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(reponse.data[0]["theme"], "Robotique avancee")

    def test_filtre_after_date(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.get(reverse("sessions_app:list-create"), {"after_date": "2026-10-14"})

        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(reponse.data[0]["theme"], "Soudure")

    def test_filtre_recherche(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.get(reverse("sessions_app:list-create"), {"search": "robotique"})

        self.assertEqual(len(reponse.data), 1)
        self.assertEqual(reponse.data[0]["theme"], "Robotique avancee")

    def test_un_membre_peut_lister_les_seances(self):
        self.client.force_authenticate(user=self.membre)
        reponse = self.client.get(reverse("sessions_app:list-create"))

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reponse.data), 2)


class ReservationApresCoupTests(BaseSeanceTests):
    def test_ajout_de_materiel_sur_une_seance_existante(self):
        seance = Session.objects.create(
            date=timezone.now(), location="salle 004", theme="Test"
        )
        self.client.force_authenticate(user=self.staff)

        reponse = self.client.post(
            reverse("sessions_app:reserve-equipment", args=[seance.id]),
            {"equipment_id": self.cartes.id, "quantity_reserved": 3},
            format="json",
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reponse.data["equipments"]), 1)
        self.assertEqual(reponse.data["equipments"][0]["quantity_reserved"], 3)

    def test_second_appel_met_a_jour_la_quantite(self):
        seance = Session.objects.create(
            date=timezone.now(), location="salle 004", theme="Test"
        )
        self.client.force_authenticate(user=self.staff)
        url = reverse("sessions_app:reserve-equipment", args=[seance.id])

        self.client.post(url, {"equipment_id": self.cartes.id, "quantity_reserved": 3}, format="json")
        reponse = self.client.post(
            url, {"equipment_id": self.cartes.id, "quantity_reserved": 7}, format="json"
        )

        self.assertEqual(reponse.status_code, status.HTTP_200_OK)
        self.assertEqual(seance.equipment_reservations.count(), 1)
        self.assertEqual(reponse.data["equipments"][0]["quantity_reserved"], 7)
