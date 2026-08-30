from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class UsersAPITests(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="AdminPassword123!",
            matricule=1000,
            is_approved=True
        )

        self.approved_user = User.objects.create_user(
            username="user_approved",
            email="approved@example.com",
            password="UserPassword123!",
            matricule=2000,
            is_approved=True
        )

        self.pending_user = User.objects.create_user(
            username="user_pending",
            email="pending@example.com",
            password="UserPassword123!",
            matricule=3000,
            is_approved=False
        )

        self.register_url = reverse('auth_register')
        self.login_url = reverse('token_obtain_pair')
        self.pending_list_url = reverse('pending_users')

    def test_register_user_success(self):
        payload = {
            "username": "martin",
            "email": "martin@example.com",
            "password": "motdepassesecurise",
            "matricule": 2826
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_approved'])
        self.assertTrue(User.objects.filter(username="martin").exists())

    def test_login_approved_user_success(self):
        payload = {
            "matricule": 2000,
            "password": "UserPassword123!"
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_pending_user_returns_403(self):
        payload = {
            "matricule": 3000,
            "password": "UserPassword123!"
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    def test_get_pending_users_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.pending_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user_pending')

    def test_get_pending_users_as_unauthorized_fails(self):
        self.client.force_authenticate(user=self.approved_user)
        response = self.client.get(self.pending_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_user_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        # On utilise le matricule comme clé primaire (pk)
        approve_url = reverse('approve_user', kwargs={'pk': self.pending_user.matricule})
        payload = {"is_approved": True}
        
        response = self.client.patch(approve_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.is_approved)

    def test_change_role_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        role_url = reverse('change_role', kwargs={'pk': self.approved_user.matricule})
        response = self.client.patch(role_url, {"role": "STAFF"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approved_user.refresh_from_db()
        self.assertEqual(self.approved_user.role, "STAFF")

    def test_change_role_forbidden_for_non_admin(self):
        self.client.force_authenticate(user=self.approved_user)
        role_url = reverse('change_role', kwargs={'pk': self.pending_user.matricule})
        response = self.client.patch(role_url, {"role": "ADMIN"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_ignores_role_in_payload(self):
        """Vérifie qu'on ne peut pas s'auto-attribuer un rôle à l'inscription."""
        payload = {
            "username": "hacker",
            "email": "hacker@example.com",
            "password": "motdepassesecurise",
            "matricule": 9999,
            "role": "ADMIN",
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(matricule=9999)
        self.assertEqual(created.role, "MEMBER")