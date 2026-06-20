from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.users.models import User, Company # Utilisation directe des modèles pour la configuration des tests
from .models import Client
# Il est souvent utile d'utiliser des factories pour créer des données de test
# from .factories import UserFactory, CompanyFactory, ClientFactory # Si on utilisait factory_boy

class ClientAPITests(APITestCase):
    def setUp(self):
        # Utilisateur 1 et sa société
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='password123',
            first_name='User',
            last_name='One'
        )
        self.company1 = Company.objects.create(name="User1 Company", owner=self.user1)

        # Utilisateur 2 et sa société
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='password123',
            first_name='User',
            last_name='Two'
        )
        self.company2 = Company.objects.create(name="User2 Company", owner=self.user2)

        # Client pour company1
        self.client1_c1 = Client.objects.create(
            company_account=self.company1,
            client_name="Client Alpha of Company1"
        )
        # Autre client pour company1
        self.client2_c1 = Client.objects.create(
            company_account=self.company1,
            client_name="Client Beta of Company1"
        )
        # Client pour company2
        self.client1_c2 = Client.objects.create(
            company_account=self.company2,
            client_name="Client Gamma of Company2"
        )

        self.client = APIClient() # Client pour faire des requêtes API

    def test_unauthenticated_user_cannot_access_clients(self):
        """
        Vérifie que les utilisateurs non authentifiés ne peuvent pas accéder aux endpoints des clients.
        """
        list_url = reverse('clients_api:client-list') # 'clients_api' est l'app_name, 'client-list' est le nom généré par le router
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        detail_url = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list_own_company_clients(self):
        """
        Vérifie qu'un utilisateur authentifié peut lister les clients de ses sociétés.
        """
        self.client.force_authenticate(user=self.user1)
        list_url = reverse('clients_api:client-list')
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # user1 a 2 clients dans company1
        client_names = [item['client_name'] for item in response.data['results']]
        self.assertIn(self.client1_c1.client_name, client_names)
        self.assertIn(self.client2_c1.client_name, client_names)
        self.assertNotIn(self.client1_c2.client_name, client_names) # Ne doit pas voir le client de company2

    def test_authenticated_user_cannot_list_other_company_clients(self):
        """
        Vérifie qu'un utilisateur authentifié ne voit pas les clients d'une autre société
        s'il n'y a pas de filtrage par company_account explicite dans la requête GET
        (le ViewSet doit le faire automatiquement basé sur l'utilisateur).
        """
        self.client.force_authenticate(user=self.user2) # user2 ne devrait voir que client1_c2
        list_url = reverse('clients_api:client-list')
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['client_name'], self.client1_c2.client_name)

    def test_create_client_for_own_company(self):
        """
        Vérifie qu'un utilisateur peut créer un client pour sa propre société.
        La company_account devrait être assignée automatiquement ou validée.
        """
        self.client.force_authenticate(user=self.user1)
        create_url = reverse('clients_api:client-list')
        data = {
            "client_name": "New Client for Company1",
            "email": "newclient@company1.com",
            # company_account sera géré par perform_create dans le ViewSet
        }
        response = self.client.post(create_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 4) # 3 initiaux + 1 nouveau
        new_client = Client.objects.get(client_name="New Client for Company1")
        self.assertEqual(new_client.company_account, self.company1)
        self.assertEqual(new_client.email, "newclient@company1.com")

    def test_create_client_fails_if_user_has_no_company(self):
        """
        Vérifie que la création de client échoue si l'utilisateur n'a pas de société.
        (Nécessite un utilisateur sans société pour ce test)
        """
        user_no_company = User.objects.create_user(email='nocorp@example.com', username='nocorp', password='password123')
        self.client.force_authenticate(user=user_no_company)
        create_url = reverse('clients_api:client-list')
        data = {"client_name": "Client for No Company User"}
        response = self.client.post(create_url, data, format='json')
        # S'attend à une erreur car perform_create ne trouvera pas de société pour cet utilisateur
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_account", response.data) # Ou une clé d'erreur générale

    def test_user_cannot_create_client_for_another_users_company_explicitly(self):
        """
        Vérifie qu'un utilisateur ne peut pas créer un client en spécifiant
        explicitement la company_account d'un autre utilisateur si la validation est en place.
        """
        self.client.force_authenticate(user=self.user1)
        create_url = reverse('clients_api:client-list')
        data = {
            "client_name": "Sneaky Client",
            "company_account": self.company2.pk # Tente d'assigner à company2 de user2
        }
        response = self.client.post(create_url, data, format='json')
        # Le perform_create devrait soit ignorer le company_account fourni et utiliser celui de user1,
        # soit lever une ValidationError si company_account est fourni et n'appartient pas à user1.
        # Le comportement exact dépend de l'implémentation de perform_create et du serializer.
        # Si perform_create force la compagnie de l'utilisateur :
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # sneaky_client = Client.objects.get(client_name="Sneaky Client")
        # self.assertEqual(sneaky_client.company_account, self.company1)
        # Si le serializer ou perform_create valide l'ID de company_account fourni :
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_account", response.data)


    def test_user_can_retrieve_own_company_client_detail(self):
        """
        Vérifie qu'un utilisateur peut voir les détails d'un client de sa société.
        """
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['client_name'], self.client1_c1.client_name)

    def test_user_cannot_retrieve_other_company_client_detail(self):
        """
        Vérifie qu'un utilisateur ne peut pas voir les détails d'un client d'une autre société.
        """
        self.client.force_authenticate(user=self.user1)
        detail_url_other_company = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c2.pk})
        response = self.client.get(detail_url_other_company)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Ou 403 si la permission est plus explicite

    def test_user_can_update_own_company_client(self):
        """
        Vérifie qu'un utilisateur peut mettre à jour un client de sa société.
        """
        self.client.force_authenticate(user=self.user1)
        update_url = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c1.pk})
        data = {"client_name": "Client Alpha Updated", "email": "alpha_updated@company1.com"}
        response = self.client.put(update_url, data, format='json') # PUT pour mise à jour complète

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client1_c1.refresh_from_db()
        self.assertEqual(self.client1_c1.client_name, "Client Alpha Updated")
        self.assertEqual(self.client1_c1.email, "alpha_updated@company1.com")

    def test_user_cannot_update_other_company_client(self):
        """
        Vérifie qu'un utilisateur ne peut pas mettre à jour un client d'une autre société.
        """
        self.client.force_authenticate(user=self.user1)
        update_url_other_company = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c2.pk})
        data = {"client_name": "Attempted Update"}
        response = self.client.put(update_url_other_company, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Ou 403

    def test_user_can_delete_own_company_client(self):
        """
        Vérifie qu'un utilisateur peut supprimer un client de sa société.
        """
        self.client.force_authenticate(user=self.user1)
        delete_url = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c1.pk})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(pk=self.client1_c1.pk).exists())

    def test_user_cannot_delete_other_company_client(self):
        """
        Vérifie qu'un utilisateur ne peut pas supprimer un client d'une autre société.
        """
        self.client.force_authenticate(user=self.user1)
        delete_url_other_company = reverse('clients_api:client-detail', kwargs={'pk': self.client1_c2.pk})
        response = self.client.delete(delete_url_other_company)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Ou 403
        self.assertTrue(Client.objects.filter(pk=self.client1_c2.pk).exists())
