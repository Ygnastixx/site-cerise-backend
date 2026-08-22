from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Equipment


User = get_user_model()


class EquipmentAPITestCase(APITestCase):

    def setUp(self):
        """Configuration initiale exécutée avant chaque test."""

        # Création d'un utilisateur de test
        self.user = User.objects.create_user(
            matricule="2954",
            username="inventorytest",
            email="inventory@example.com",
            password="Password123!",
            role="MEMBER",
            is_approved=True,
        )

        # Génération du token JWT
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # URL de la liste des équipements
        self.url = reverse("equipment-list-create")

        # Création d'un équipement de test
        self.equipment = Equipment.objects.create(
            name="Caméra",
            brand="Sony",
            model="A7 III",
            purchase_price="1500.00",
            quantity=2,
            description="Caméra pour les séances",
        )

    def test_get_equipments_success(self):
        """Vérifie la récupération des équipements."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data),
            1
        )

        self.assertEqual(
            response.data[0]["name"],
            "Caméra"
        )

    def test_create_equipment_success(self):
        """Vérifie la création d'un équipement."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        payload = {
            "name": "Microphone",
            "brand": "Rode",
            "model": "NT1",
            "purchase_price": "500.00",
            "quantity": 3,
            "description": "Microphone pour les séances",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["name"],
            "Microphone"
        )

        self.assertEqual(
            Equipment.objects.count(),
            2
        )

    def test_update_equipment_success(self):
        """Vérifie la modification complète d'un équipement."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        url = reverse(
            "equipment-detail",
            kwargs={"pk": self.equipment.id}
        )

        payload = {
            "name": "Caméra mise à jour",
            "brand": "Sony",
            "model": "A7 III",
            "purchase_price": "1600.00",
            "quantity": 3,
            "description": "Caméra mise à jour",
        }

        response = self.client.put(
            url,
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["name"],
            "Caméra mise à jour"
        )

        # Vérifie que la modification est réellement enregistrée
        self.equipment.refresh_from_db()

        self.assertEqual(
            self.equipment.name,
            "Caméra mise à jour"
        )