from django.test import TestCase, Client as DjangoClient # Renommer pour éviter confusion avec APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.models import Company # Importer Company
# from unittest.mock import patch # Pour mocker les appels requests.post à l'API

User = get_user_model()

# TODO: Mocker les appels `requests.post` pour isoler les tests des vues web de la disponibilité réelle de l'API.
# Pour l'instant, ces tests sont plus des tests d'intégration car ils vont essayer d'appeler l'API.

class UserAuthWebTests(TestCase):
    def setUp(self):
        self.client = DjangoClient() # Client de test Django pour les vues web
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')
        self.dashboard_url = reverse('dashboard:main') # Assurez-vous que cette URL est définie

        self.user_data_form = {
            'username': 'webtestuser',
            'email': 'webtestuser@example.com',
            'first_name': 'WebTest',
            'last_name': 'User',
            'company_name': 'Web Test Corp',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }
        self.login_creds = { # Pour le formulaire de login Django
            'username': 'webtestuser@example.com', # AuthenticationForm utilise 'username' pour le champ login
            'password': 'StrongPassword123!',
        }
        # Données pour l'appel API simulé (si on mocke)
        self.api_register_success_response = {
            "message": "Inscription réussie.",
            "user": {"id": "some-uuid", "email": "webtestuser@example.com", "username": "webtestuser"},
            "token": "fakeapitoken123",
            "default_company_id": "some-company-uuid"
        }
        self.api_login_success_response = {
            "token": "fakeapitoken123",
            "user": {"id": "some-uuid", "email": "webtestuser@example.com", "username": "webtestuser"},
            "active_company_id": "some-company-uuid",
            "active_company_name": "Web Test Corp"
        }

    # @patch('requests.post') # Décommenter et configurer le mock si on veut isoler
    def test_user_registration_view_success(self, mock_api_post=None):
        # if mock_api_post: # Configurer le mock
        #     mock_response = mock_api_post.return_value
        #     mock_response.status_code = 201
        #     mock_response.json.return_value = self.api_register_success_response

        #     # Il faut aussi mocker l'authenticate de Django car l'user n'existera pas vraiment
        #     # si l'appel API est complètement mocké et ne crée pas l'user en BDD.
        #     # C'est là que les tests deviennent complexes à mocker entièrement.
        #     # Pour l'instant, on fait un test plus intégré.

        # Créer l'utilisateur et la société via l'API pour que authenticate fonctionne
        # Ceci est un test d'intégration de la vue web qui dépend de l'API UserRegistrationView fonctionnant.
        api_client = self.client # Utiliser le même client pour la simplicité ici
        api_register_url = reverse('users_api:register')
        api_response = api_client.post(api_register_url, {
            'username': self.user_data_form['username'],
            'email': self.user_data_form['email'],
            'password': self.user_data_form['password'],
            'password2': self.user_data_form['password2'],
            'first_name': self.user_data_form['first_name'],
            'last_name': self.user_data_form['last_name'],
            'company_name': self.user_data_form['company_name'],
        }, format='json')
        self.assertEqual(api_response.status_code, status.HTTP_201_CREATED, "L'API d'inscription doit fonctionner pour ce test.")

        # Maintenant, tester la vue web de login avec cet utilisateur
        # (Le test de la vue d'inscription web est un peu redondant si l'API est appelée directement,
        # mais on peut tester le rendu du formulaire et la redirection)

        # Test GET de la page d'inscription
        response_get = self.client.get(self.register_url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response_get, 'users/register.html')

        # Test POST de la page d'inscription (en utilisant un nouvel utilisateur pour éviter conflit)
        new_user_data_form = self.user_data_form.copy()
        new_user_data_form['username'] = 'webtestuser2'
        new_user_data_form['email'] = 'webtestuser2@example.com'

        response_post = self.client.post(self.register_url, new_user_data_form)

        # Vérifier la redirection vers le dashboard après inscription réussie
        # La vue d'inscription appelle l'API, puis logue l'utilisateur.
        self.assertRedirects(response_post, self.dashboard_url, status_code=302, target_status_code=200)
        self.assertTrue(User.objects.filter(username='webtestuser2').exists(), "L'utilisateur aurait dû être créé via l'API appelée par la vue.")

        # Vérifier que l'utilisateur est connecté dans la session Django
        # Pour cela, il faut faire une requête authentifiée après la redirection
        # response_dashboard = self.client.get(self.dashboard_url) # Le client suit la redirection
        # self.assertTrue(response_dashboard.context['user'].is_authenticated) # Ne fonctionne pas directement comme ça
        user_is_authenticated = '_auth_user_id' in self.client.session
        self.assertTrue(user_is_authenticated, "L'utilisateur devrait être connecté dans la session Django après inscription.")


    def test_user_login_view_success_and_session(self):
        # 1. Créer l'utilisateur via l'API pour s'assurer qu'il existe
        api_client = self.client
        api_register_url = reverse('users_api:register')
        api_response = api_client.post(api_register_url, self.user_data_form, format='json')
        self.assertEqual(api_response.status_code, status.HTTP_201_CREATED, "L'API d'inscription doit fonctionner.")

        # 2. Tester la vue de connexion web
        response = self.client.post(self.login_url, self.login_creds)
        self.assertRedirects(response, self.dashboard_url, status_code=302, target_status_code=200)

        # Vérifier que le token API et active_company_id sont en session
        self.assertIn('api_auth_token', self.client.session)
        self.assertIsNotNone(self.client.session['api_auth_token'])
        self.assertIn('active_company_id', self.client.session)
        self.assertIsNotNone(self.client.session['active_company_id'])

        # Vérifier que l'utilisateur est authentifié dans la session Django
        user_is_authenticated = '_auth_user_id' in self.client.session
        self.assertTrue(user_is_authenticated)


    def test_user_login_view_failure(self):
        response = self.client.post(self.login_url, {'username': 'wrong@example.com', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Reste sur la page de login
        self.assertFormError(response, 'form', None, 'Please enter a correct email ou nom d\'utilisateur and password. Note that both fields may be case-sensitive.') # Message d'erreur d'AuthenticationForm
        # Ou si on personnalise le message :
        # self.assertContains(response, "Email ou mot de passe incorrect.")


    def test_user_logout_view(self):
        # D'abord, inscrire et connecter un utilisateur
        api_client = self.client
        api_register_url = reverse('users_api:register')
        api_client.post(api_register_url, self.user_data_form, format='json')
        self.client.post(self.login_url, self.login_creds) # Connecte et met des choses en session

        self.assertIn('api_auth_token', self.client.session)
        self.assertIn('_auth_user_id', self.client.session)

        # Tester la déconnexion
        response = self.client.post(self.logout_url) # La vue de logout est souvent un POST pour éviter CSRF sur un GET
        self.assertRedirects(response, self.login_url, status_code=302, target_status_code=200)

        # Vérifier que la session a été nettoyée
        self.assertNotIn('api_auth_token', self.client.session)
        self.assertNotIn('active_company_id', self.client.session)
        user_is_authenticated_after_logout = '_auth_user_id' in self.client.session # Devrait être false
        self.assertFalse(user_is_authenticated_after_logout)

    def test_authenticated_user_redirected_from_login_register(self):
        # Inscrire et connecter
        api_client = self.client
        api_register_url = reverse('users_api:register')
        api_client.post(api_register_url, self.user_data_form, format='json')
        self.client.post(self.login_url, self.login_creds)

        # Tenter d'accéder à la page de login
        response_login = self.client.get(self.login_url)
        self.assertRedirects(response_login, self.dashboard_url, status_code=302, target_status_code=200)

        # Tenter d'accéder à la page d'inscription
        response_register = self.client.get(self.register_url)
        self.assertRedirects(response_register, self.dashboard_url, status_code=302, target_status_code=200)

    # Ajouter des tests pour la vue de profil quand elle sera plus complète
    # def test_user_profile_view_get(self):
    #     # ...
    # def test_user_profile_view_post_update(self):
    #     # ...
