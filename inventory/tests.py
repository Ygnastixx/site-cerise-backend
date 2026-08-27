from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Equipment

User = get_user_model()


class InventoryAPITestCase(APITestCase):

    def setUp(self):
        # 1. Staff approuvé (Accès complet)
        self.staff_user = User.objects.create_user(
            matricule="1001",
            username="staff1",
            password="Password123!",
            is_approved=True,
            role="STAFF",
            is_staff=True
        )

        # 2. Membre normal approuvé (Accès refusé par la permission)
        self.normal_user = User.objects.create_user(
            matricule="2002",
            username="member1",
            password="Password123!",
            is_approved=True,
            role="MEMBER"
        )

        # Configuration du client API et des tokens JWT
        self.client = APIClient()
        self.staff_token = str(RefreshToken.for_user(self.staff_user).access_token)
        self.member_token = str(RefreshToken.for_user(self.normal_user).access_token)

        # Création d'un équipement initial avec les champs réels du modèle
        self.equipment = Equipment.objects.create(
            name="Imprimante 3D",
            brand="Creality",
            model="Ender 3 V2",
            purchase_price="250.00",
            quantity=2,
            description="Imprimante FDM pour la fabrication de pièces TCG et prototypes."
        )

        # Les URLs (remplace par le name configuré dans tes urls.py si différent)
        self.list_url = reverse("equipment-list-create")
        self.detail_url = reverse("equipment-detail", kwargs={"pk": self.equipment.pk})

    def authenticate(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # ==========================================
    # 1. TESTS DES PERMISSIONS
    # ==========================================

    def test_unauthenticated_user_cannot_access_inventory(self):
        """Un utilisateur anonyme ne peut pas accéder à l'inventaire."""
        self.client.credentials()
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_normal_member_forbidden_access(self):
        """Un membre normal ne peut ni voir ni créer d'équipement."""
        self.authenticate(self.member_token)
        response_get = self.client.get(self.list_url)
        payload = {
            "name": "Oscilloscope",
            "brand": "Rigol",
            "model": "DS1054Z",
            "purchase_price": "350.00",
            "quantity": 1,
            "description": "Mesure de signaux électroniques."
        }
        response_post = self.client.post(self.list_url, payload, format="json")
        
        self.assertEqual(response_get.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response_post.status_code, status.HTTP_403_FORBIDDEN)

    # ==========================================
    # 2. TESTS DU CRUD PAR LE STAFF
    # ==========================================

    def test_staff_can_list_equipment(self):
        """Le staff approuvé peut récupérer la liste des équipements."""
        self.authenticate(self.staff_token)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Imprimante 3D")

    def test_staff_can_create_equipment(self):
        """Le staff approuvé peut créer un équipement valide."""
        self.authenticate(self.staff_token)
        payload = {
            "name": "Fer à souder",
            "brand": "Pinecil",
            "model": "V2",
            "purchase_price": "45.50",
            "quantity": 5,
            "description": "Station de soudage portable pour ateliers mechatronique."
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Equipment.objects.count(), 2)

    def test_staff_can_update_equipment(self):
        """Le staff peut mettre à jour un équipement via la vue de détail."""
        self.authenticate(self.staff_token)
        payload = {
            "name": "Imprimante 3D Pro",
            "brand": "Creality",
            "model": "Ender 3 V2",
            "purchase_price": "250.00",
            "quantity": 3,
            "description": "Mise à jour de la quantité et du nom."
        }
        response = self.client.put(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.equipment.refresh_from_db()
        self.assertEqual(self.equipment.quantity, 3)

    # ==========================================
    # 3. TESTS DE VALIDATION DES CODES D'ERREUR HTTP 400
    # ==========================================

    def test_invalid_payload_returns_400_bad_request(self):
        """Une erreur de validation lors du POST doit renvoyer 400 et non 401/404."""
        self.authenticate(self.staff_token)
        payload = {
            "name": "",  # Nom invalide
            "brand": "Inconnue",
            "model": "X",
            "purchase_price": "prix_invalide",  # Price invalide
            "quantity": -1,
            "description": "Test"
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)