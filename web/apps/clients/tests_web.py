from django.test import TestCase, Client as DjangoClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.models import Company # Pour créer une société de test
from unittest.mock import patch, MagicMock # Pour mocker requests.get

User = get_user_model()

class ClientListViewWebTests(TestCase):
    def setUp(self):
        self.django_client = DjangoClient() # Client de test Django
        self.list_url = reverse('clients:list')

        # Créer un utilisateur et une société pour les tests
        self.test_user = User.objects.create_user(
            username='testclientuser',
            email='clientuser@example.com',
            password='password123',
            first_name='Client',
            last_name='Tester'
        )
        self.test_company = Company.objects.create(name="Client Test Co", owner=self.test_user)

        # Simuler la connexion de l'utilisateur et la configuration de la session
        # Note: Le login via self.django_client.login() ne remplit pas la session
        # avec nos clés personnalisées comme 'api_auth_token' ou 'active_company_id'.
        # Nous devons les ajouter manuellement à la session du client de test.

        # D'abord, connecter l'utilisateur pour avoir une session Django valide
        self.django_client.login(username='clientuser@example.com', password='password123')

        # Ensuite, ajouter manuellement les clés de session que nos vues attendent
        session = self.django_client.session
        session['api_auth_token'] = 'faketesttoken123'
        session['active_company_id'] = str(self.test_company.id) # Doit être une string si UUID
        session['active_company_name'] = self.test_company.name
        session.save()

        # Données de réponse API mockées pour la liste des clients
        self.mock_api_client_list_page1 = {
            "count": 2,
            "next": f"http://localhost:8000/api/v1/clients/?company_account_id={self.test_company.id}&page=2",
            "previous": None,
            "results": [
                {"id": "uuid1", "client_name": "Client Alpha", "email": "alpha@example.com", "phone": "111", "is_active": True, "created_at": "2023-01-01T10:00:00Z"},
                {"id": "uuid2", "client_name": "Client Beta", "email": "beta@example.com", "phone": "222", "is_active": False, "created_at": "2023-01-02T11:00:00Z"},
            ]
        }
        self.mock_api_client_list_page2 = {
            "count": 2, # Supposons qu'il n'y a que 2 clients au total pour ce test de pagination
            "next": None,
            "previous": f"http://localhost:8000/api/v1/clients/?company_account_id={self.test_company.id}&page=1",
            "results": [] # Pas d'autres résultats sur la page 2 pour cet exemple
        }
        self.mock_api_empty_list = {
            "count": 0, "next": None, "previous": None, "results": []
        }


    def test_client_list_view_unauthenticated_redirects_to_login(self):
        self.django_client.logout() # S'assurer que l'utilisateur est déconnecté
        response = self.django_client.get(self.list_url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.list_url}")

    def test_client_list_view_no_api_token_redirects_to_login(self):
        session = self.django_client.session
        if 'api_auth_token' in session:
            del session['api_auth_token']
        session.save()
        response = self.django_client.get(self.list_url)
        # La vue devrait détecter l'absence de token et rediriger
        self.assertRedirects(response, reverse('users:login'))
        # messages = list(response.context['messages'])
        # self.assertEqual(len(messages), 1)
        # self.assertEqual(str(messages[0]), "Erreur d'authentification API. Veuillez vous reconnecter.")


    def test_client_list_view_no_active_company_redirects_to_dashboard(self):
        session = self.django_client.session
        if 'active_company_id' in session:
            del session['active_company_id']
        session.save()
        response = self.django_client.get(self.list_url)
        # La vue redirige vers le dashboard si pas de société active
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))


    @patch('requests.get')
    def test_client_list_view_displays_clients_from_api(self, mock_api_get):
        # Configurer le mock pour retourner les données de la page 1
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_client_list_page1
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_list.html')
        self.assertContains(response, "Client Alpha")
        self.assertContains(response, "Client Beta")
        self.assertIn('clients_data', response.context)
        self.assertEqual(len(response.context['clients_data']['results']), 2)

        # Vérifier que l'appel API a été fait avec les bons params
        expected_api_url = f"http://localhost:8000/api/v1/clients/"
        expected_params = {'company_account_id': str(self.test_company.id), 'page': 1}
        mock_api_get.assert_called_once_with(
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken123'},
            params=expected_params
        )

    @patch('requests.get')
    def test_client_list_view_handles_api_error(self, mock_api_get):
        mock_response = MagicMock()
        mock_response.status_code = 500 # Simuler une erreur serveur de l'API
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.list_url)
        self.assertEqual(response.status_code, 200) # La vue gère l'erreur et rend la page
        self.assertContains(response, "Erreur lors de la récupération des clients")
        self.assertIsNone(response.context['clients_data']) # ou une structure vide selon la gestion d'erreur

    @patch('requests.get')
    def test_client_list_view_htmx_request_renders_partial(self, mock_api_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_client_list_page1
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.list_url, HTTP_HX_REQUEST='true') # Simuler une requête HTMX
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/partials/_client_list_table.html')
        self.assertContains(response, "Client Alpha") # Vérifier que les données sont dans le partiel

    @patch('requests.get')
    def test_client_list_view_search_filter(self, mock_api_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simuler une réponse API filtrée
        filtered_response_data = {
            "count": 1, "next": None, "previous": None,
            "results": [{"id": "uuid1", "client_name": "Client Alpha Searched", "email": "alpha@example.com"}]
        }
        mock_response.json.return_value = filtered_response_data
        mock_api_get.return_value = mock_response

        search_term = "Alpha Searched"
        response = self.django_client.get(self.list_url, {'search_query': search_term, 'is_active': 'true'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Client Alpha Searched")

        expected_api_url = f"http://localhost:8000/api/v1/clients/"
        expected_params = {
            'company_account_id': str(self.test_company.id),
            'page': 1, # Page par défaut
            'search': search_term,
            'is_active': 'true'
        }
        mock_api_get.assert_called_with( # Utiliser assert_called_with car il peut y avoir eu un appel précédent dans d'autres tests si pas bien isolé
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken123'},
            params=expected_params
        )
        self.assertEqual(response.context['search_query'], search_term)
        self.assertEqual(response.context['status_filter'], 'true')


    @patch('requests.get')
    def test_client_list_view_pagination_htmx(self, mock_api_get):
        # Premier appel pour la page 1
        mock_page1_response = MagicMock()
        mock_page1_response.status_code = 200
        mock_page1_response.json.return_value = self.mock_api_client_list_page1

        # Deuxième appel pour la page 2 (simulé par le lien de pagination)
        mock_page2_response = MagicMock()
        mock_page2_response.status_code = 200
        mock_page2_response.json.return_value = self.mock_api_client_list_page2 # Devrait être vide ou avoir d'autres items

        # Configurer le mock pour retourner différentes valeurs à chaque appel
        mock_api_get.side_effect = [mock_page1_response, mock_page2_response]

        # Charger la page 1 initialement (non-HTMX pour avoir le contexte complet)
        response_page1_full = self.django_client.get(self.list_url)
        self.assertEqual(response_page1_full.status_code, 200)
        self.assertContains(response_page1_full, "Client Alpha")
        # S'assurer que le lien 'next' est présent si mock_api_client_list_page1.next est non-null
        if self.mock_api_client_list_page1['next']:
            self.assertContains(response_page1_full, 'Suivant &raquo;')

        # Simuler un clic HTMX sur le lien de pagination vers la page 2
        # L'URL du lien "next" vient de mock_api_client_list_page1
        next_page_url_params = self.mock_api_client_list_page1['next'].split('?')[-1] # ex: "company_account_id=...&page=2"

        response_page2_htmx = self.django_client.get(f"{self.list_url}?{next_page_url_params}", HTTP_HX_REQUEST='true')
        self.assertEqual(response_page2_htmx.status_code, 200)
        self.assertTemplateUsed(response_page2_htmx, 'clients/partials/_client_list_table.html')
        # La page 2 de notre mock est vide, donc on ne devrait pas trouver les clients de la page 1
        self.assertNotContains(response_page2_htmx, "Client Alpha")

        # Vérifier les appels à l'API mockée
        self.assertEqual(mock_api_get.call_count, 2)
        # Premier appel (page 1)
        call1_args, call1_kwargs = mock_api_get.call_args_list[0]
        self.assertEqual(call1_kwargs['params']['page'], 1)
        # Deuxième appel (page 2)
        call2_args, call2_kwargs = mock_api_get.call_args_list[1]
        self.assertEqual(call2_kwargs['params']['page'], '2') # Page est une string dans les query params
        self.assertEqual(call2_kwargs['params']['company_account_id'], str(self.test_company.id))

    # Ajouter des tests pour le ClientFilterForm si besoin (ex: validation, champs)
    # Ajouter des tests pour la vue de création quand elle sera implémentée.
