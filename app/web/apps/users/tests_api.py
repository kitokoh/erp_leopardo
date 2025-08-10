from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import Company
from rest_framework.authtoken.models import Token

User = get_user_model()

class UserAuthAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('users_api:register')
        self.login_url = reverse('users_api:login')
        self.me_url = reverse('users_api:me')

        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company_name': 'Test User Inc.'
        }
        self.user_login_data = {
            'email': 'testuser@example.com', # Ou username si USERNAME_FIELD est username
            'password': 'StrongPassword123!'
        }

        # Un autre utilisateur pour les tests de permissions
        self.other_user_data = {
            'username': 'otheruser',
            'email': 'otheruser@example.com',
            'password': 'OtherPassword123!',
            'password2': 'OtherPassword123!',
            'first_name': 'Other',
            'last_name': 'User',
            'company_name': 'Other User Corp.'
        }


    # === User Registration Tests ===
    def test_user_registration_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertIn('default_company_id', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        # Vérifier que la société par défaut a été créée
        created_user = User.objects.get(email=self.user_data['email'])
        self.assertTrue(Company.objects.filter(owner=created_user, name=self.user_data['company_name']).exists())

    def test_user_registration_default_company_name(self):
        data_no_company_name = self.user_data.copy()
        data_no_company_name.pop('company_name')
        response = self.client.post(self.register_url, data_no_company_name, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.get(email=data_no_company_name['email'])
        expected_company_name = f"Société de {created_user.username}"
        self.assertTrue(Company.objects.filter(owner=created_user, name=expected_company_name).exists())


    def test_user_registration_passwords_mismatch(self):
        data = self.user_data.copy()
        data['password2'] = 'WrongPassword!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data)

    def test_user_registration_email_taken(self):
        self.client.post(self.register_url, self.user_data, format='json') # First user
        response = self.client.post(self.register_url, self.user_data, format='json') # Attempt again
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_user_registration_username_taken(self):
        self.client.post(self.register_url, self.user_data, format='json') # First user
        data_same_username = self.user_data.copy()
        data_same_username['email'] = 'newemail@example.com' # Different email
        response = self.client.post(self.register_url, data_same_username, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_user_registration_missing_required_fields(self):
        # Test missing email
        data_no_email = self.user_data.copy()
        data_no_email.pop('email')
        response = self.client.post(self.register_url, data_no_email, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

        # Test missing username
        data_no_username = self.user_data.copy()
        data_no_username.pop('username')
        response = self.client.post(self.register_url, data_no_username, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

        # Test missing password
        data_no_password = self.user_data.copy()
        data_no_password.pop('password')
        response = self.client.post(self.register_url, data_no_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    # === User Login Tests ===
    def test_user_login_success(self):
        self.client.post(self.register_url, self.user_data, format='json') # Register first
        response = self.client.post(self.login_url, self.user_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertIn('active_company_id', response.data)
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_user_login_invalid_credentials(self):
        self.client.post(self.register_url, self.user_data, format='json')
        invalid_data = {'email': self.user_data['email'], 'password': 'WrongPassword!'}
        response = self.client.post(self.login_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # ObtainAuthToken returns 400
        self.assertIn('non_field_errors', response.data)

    def test_user_login_inactive_user(self):
        # Register user
        self.client.post(self.register_url, self.user_data, format='json')
        # Deactivate user
        user_obj = User.objects.get(email=self.user_data['email'])
        user_obj.is_active = False
        user_obj.save()

        response = self.client.post(self.login_url, self.user_login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data) # Default "Unable to log in with provided credentials."

    # === User Detail (me) Tests ===
    def test_get_user_me_authenticated(self):
        # Register and login user
        reg_response = self.client.post(self.register_url, self.user_data, format='json')
        token = reg_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertIn('owned_companies', response.data) # Vérifier que les sociétés sont là
        self.assertTrue(len(response.data['owned_companies']) > 0)
        self.assertEqual(response.data['owned_companies'][0]['name'], self.user_data['company_name'])


    def test_get_user_me_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_me_authenticated(self):
        reg_response = self.client.post(self.register_url, self.user_data, format='json')
        token = reg_response.data['token']
        user_obj = User.objects.get(email=self.user_data['email'])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        update_data = {'first_name': 'UpdatedFirst', 'last_name': 'UpdatedLast'}
        response = self.client.put(self.me_url, update_data, format='json') # PUT ou PATCH
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'UpdatedFirst')
        user_obj.refresh_from_db()
        self.assertEqual(user_obj.first_name, 'UpdatedFirst')

        # Test que l'email/username ne sont pas modifiés par cette vue
        update_data_disallowed = {'email': 'new@example.com', 'username': 'newusername'}
        response = self.client.put(self.me_url, update_data_disallowed, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # La vue ignore les champs non autorisés
        user_obj.refresh_from_db()
        self.assertEqual(user_obj.email, self.user_data['email']) # Doit rester inchangé
        self.assertEqual(user_obj.username, self.user_data['username']) # Doit rester inchangé


class CompanyAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.companies_url = reverse('users_api:company-list') # Pour POST et GET (liste)

        # User 1 et son token
        self.user1_data = {
            'username': 'compuser1', 'email': 'compuser1@example.com', 'password': 'Password123!',
            'password2': 'Password123!', 'first_name': 'Comp1', 'last_name': 'User1',
            'company_name': 'Comp1 Initial Ltd'
        }
        reg_response1 = self.client.post(reverse('users_api:register'), self.user1_data, format='json')
        self.user1_token = reg_response1.data['token']
        self.user1 = User.objects.get(email=self.user1_data['email'])
        self.company1_user1 = Company.objects.get(owner=self.user1, name=self.user1_data['company_name'])

        # User 2 et son token
        self.user2_data = {
            'username': 'compuser2', 'email': 'compuser2@example.com', 'password': 'Password123!',
            'password2': 'Password123!', 'first_name': 'Comp2', 'last_name': 'User2',
            'company_name': 'Comp2 Initial LLC'
        }
        reg_response2 = self.client.post(reverse('users_api:register'), self.user2_data, format='json')
        self.user2_token = reg_response2.data['token']
        self.user2 = User.objects.get(email=self.user2_data['email'])
        self.company1_user2 = Company.objects.get(owner=self.user2, name=self.user2_data['company_name'])


    def test_create_company_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        company_data = {'name': 'User1 New Company', 'address': '123 Main St'}
        response = self.client.post(self.companies_url, company_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'User1 New Company')
        self.assertTrue(Company.objects.filter(owner=self.user1, name='User1 New Company').exists())
        self.assertEqual(self.user1.owned_companies.count(), 2) # Initial + New

    def test_create_company_unauthenticated(self):
        company_data = {'name': 'Unauth Company'}
        response = self.client.post(self.companies_url, company_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_own_companies(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        # User1 crée une deuxième société
        Company.objects.create(name="User1 Second Company", owner=self.user1, address="456 Second St")

        response = self.client.get(self.companies_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2) # Initial + Second
        company_names = [c['name'] for c in response.data['results']]
        self.assertIn(self.company1_user1.name, company_names)
        self.assertIn("User1 Second Company", company_names)
        self.assertNotIn(self.company1_user2.name, company_names) # Ne doit pas voir la société de user2

    def test_retrieve_own_company_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        detail_url = reverse('users_api:company-detail', kwargs={'pk': self.company1_user1.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.company1_user1.name)

    def test_cannot_retrieve_other_user_company_detail(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        detail_url_other = reverse('users_api:company-detail', kwargs={'pk': self.company1_user2.pk})
        response = self.client.get(detail_url_other)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Car la permission filtre le queryset

    def test_update_own_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        update_url = reverse('users_api:company-detail', kwargs={'pk': self.company1_user1.pk})
        update_data = {'name': 'User1 Initial Ltd Updated', 'address': 'Updated Address'}
        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.company1_user1.refresh_from_db()
        self.assertEqual(self.company1_user1.name, 'User1 Initial Ltd Updated')

    def test_cannot_update_other_user_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        update_url_other = reverse('users_api:company-detail', kwargs={'pk': self.company1_user2.pk})
        update_data = {'name': 'Attempted Update'}
        response = self.client.put(update_url_other, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Ou 403

    def test_delete_own_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        # Créer une société spécifiquement pour ce test de suppression
        temp_company = Company.objects.create(name="To Be Deleted Co", owner=self.user1)
        delete_url = reverse('users_api:company-detail', kwargs={'pk': temp_company.pk})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Company.objects.filter(pk=temp_company.pk).exists())

    def test_cannot_delete_other_user_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        delete_url_other = reverse('users_api:company-detail', kwargs={'pk': self.company1_user2.pk})
        response = self.client.delete(delete_url_other)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Ou 403
        self.assertTrue(Company.objects.filter(pk=self.company1_user2.pk).exists())

    def test_create_company_name_uniqueness_per_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        # company1_user1 a déjà une société nommée "Comp1 Initial Ltd"
        company_data = {'name': self.company1_user1.name} # Tente de créer une autre société avec le même nom
        response = self.client.post(self.companies_url, company_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data) # Le serializer doit lever une erreur de validation

        # Mais user2 devrait pouvoir créer une société avec ce même nom
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user2_token}')
        company_data_user2 = {'name': self.company1_user1.name} # User2 utilise le nom de la société de User1
        response_user2 = self.client.post(self.companies_url, company_data_user2, format='json')
        self.assertEqual(response_user2.status_code, status.HTTP_201_CREATED) # OK pour user2
        self.assertTrue(Company.objects.filter(owner=self.user2, name=self.company1_user1.name).exists())

    def test_update_company_name_uniqueness_per_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user1_token}')
        # Créer une deuxième société pour user1
        second_company_user1 = Company.objects.create(name="User1 Second Company", owner=self.user1)

        # Tenter de renommer la deuxième société avec le nom de la première société de user1
        update_url = reverse('users_api:company-detail', kwargs={'pk': second_company_user1.pk})
        update_data = {'name': self.company1_user1.name} # Nom de la société existante de user1

        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data) # Le serializer doit lever une erreur de validation

        # Vérifier que le nom n'a pas changé
        second_company_user1.refresh_from_db()
        self.assertEqual(second_company_user1.name, "User1 Second Company")

        # Mais user1 peut renommer sa société avec un nom unique pour lui
        update_data_valid = {'name': "User1 Second Company Renamed"}
        response_valid = self.client.put(update_url, update_data_valid, format='json')
        self.assertEqual(response_valid.status_code, status.HTTP_200_OK)
        second_company_user1.refresh_from_db()
        self.assertEqual(second_company_user1.name, "User1 Second Company Renamed")
