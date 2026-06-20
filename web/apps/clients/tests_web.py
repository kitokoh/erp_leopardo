from django.test import TestCase, Client as DjangoClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.users.models import Company # Pour créer une société de test
from unittest.mock import patch, MagicMock # Pour mocker requests.get
import requests # Ajouté pour requests.exceptions.HTTPError

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

class ClientCreateViewWebTests(TestCase):
    def setUp(self):
        self.django_client = DjangoClient()
        self.create_url = reverse('clients:create')
        self.list_url = reverse('clients:list')
        self.login_url = reverse('users:login')

        self.test_user = User.objects.create_user(
            username='createclientuser',
            email='createclientuser@example.com',
            password='password123'
        )
        self.test_company = Company.objects.create(name="Create Client Test Co", owner=self.test_user)

        # Connexion et setup session
        self.django_client.login(username='createclientuser@example.com', password='password123')
        session = self.django_client.session
        session['api_auth_token'] = 'faketesttoken_create123'
        session['active_company_id'] = str(self.test_company.id)
        session['active_company_name'] = self.test_company.name
        session.save()

        self.client_form_data = {
            'client_name': 'New Web Client',
            'email': 'newweb@example.com',
            'phone': '1234567890',
            'address': '123 Web St',
            'contact_person_name': 'Web Contact',
            'contact_person_email': 'webcontact@example.com',
            'contact_person_phone': '0987654321',
            'notes': 'Test note for web creation',
            'is_active': True,
        }
        # Réponse API mockée pour une création réussie
        self.mock_api_create_success_response = {
            "id": "new-client-uuid",
            "client_name": "New Web Client",
            "email": "newweb@example.com",
            # ... autres champs ...
        }
        # Réponse API mockée pour une erreur de validation
        self.mock_api_create_fail_validation_response = {
            "client_name": ["Ce nom de client existe déjà pour cette société."],
            "email": ["Entrez une adresse email valide."]
        }

    def test_client_create_view_get_displays_form(self):
        response = self.django_client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_form.html')
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], ClientForm) # Assurez-vous d'importer ClientForm
        self.assertEqual(response.context['page_title'], 'Ajouter un Nouveau Client')

    @patch('requests.post')
    def test_client_create_view_post_success(self, mock_api_post):
        mock_response = MagicMock()
        mock_response.status_code = 201 # Création réussie
        mock_response.json.return_value = self.mock_api_create_success_response
        mock_api_post.return_value = mock_response

        response = self.django_client.post(self.create_url, self.client_form_data)

        self.assertRedirects(response, self.list_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Client 'New Web Client' créé avec succès.")

        expected_api_url = f"http://localhost:8000/api/v1/clients/"
        # Vérifier que l'appel API a été fait avec les bonnes données (sans company_account car géré par API)
        # Le ClientForm n'a pas company_account, donc il ne sera pas dans form.cleaned_data
        # Le ViewSet API ClientViewSet doit l'assigner.
        mock_api_post.assert_called_once_with(
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken_create123'},
            json=self.client_form_data # Les données envoyées à l'API sont celles du formulaire validé
        )

    def test_client_create_view_form_invalid(self):
        # Soumettre des données qui feront échouer la validation du ClientForm
        invalid_data = self.client_form_data.copy()
        invalid_data['client_name'] = '' # Nom de client vide
        response = self.django_client.post(self.create_url, invalid_data)

        self.assertEqual(response.status_code, 200) # Reste sur la page du formulaire
        self.assertTemplateUsed(response, 'clients/client_form.html')
        self.assertFormError(response, 'form', 'client_name', 'Ce champ est obligatoire.') # Ou le message de votre clean_client_name
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Veuillez corriger les erreurs" in str(m) for m in messages_list))


    @patch('requests.post')
    def test_client_create_view_api_validation_error(self, mock_api_post):
        mock_response = MagicMock()
        mock_response.status_code = 400 # Erreur de validation de l'API
        mock_response.json.return_value = self.mock_api_create_fail_validation_response
        # Simuler l'effet de raise_for_status()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_api_post.return_value = mock_response

        response = self.django_client.post(self.create_url, self.client_form_data)
        self.assertEqual(response.status_code, 200) # Reste sur la page du formulaire
        self.assertTemplateUsed(response, 'clients/client_form.html')
        # Vérifier que les erreurs de l'API sont ajoutées au formulaire
        self.assertFormError(response, 'form', 'client_name', "Ce nom de client existe déjà pour cette société.")
        self.assertFormError(response, 'form', 'email', "Entrez une adresse email valide.")


    @patch('requests.post')
    def test_client_create_view_api_server_error(self, mock_api_post):
        mock_response = MagicMock()
        mock_response.status_code = 500 # Erreur serveur de l'API
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_api_post.return_value = mock_response

        response = self.django_client.post(self.create_url, self.client_form_data)
        self.assertEqual(response.status_code, 200) # Reste sur la page
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Erreur API 500" in str(m) for m in messages_list))


    def test_client_create_view_unauthenticated(self):
        self.django_client.logout()
        response = self.django_client.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")
        response_post = self.django_client.post(self.create_url, self.client_form_data)
        self.assertRedirects(response_post, f"{self.login_url}?next={self.create_url}")

    def test_client_create_view_no_active_company(self):
        session = self.django_client.session
        del session['active_company_id']
        session.save()

        response = self.django_client.get(self.create_url)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL)) # Redirige vers dashboard par défaut
        messages_list = list(get_messages(response.wsgi_request))
        # Le message est sur la requête *avant* la redirection. Il faut suivre la redirection pour le voir.
        # Alternative: response = self.django_client.get(self.create_url, follow=True)
        # Pour l'instant, on vérifie juste la redirection.

# Nécessaire pour récupérer les messages après une redirection
from django.contrib.messages import get_messages
# Importer ClientForm depuis le bon endroit
from .forms import ClientForm # , ClientFilterForm (si on teste le form de filtre)
from django.conf import settings
from .models import Client # Importer Client pour créer une instance de test

class ClientDetailViewWebTests(TestCase):
    def setUp(self):
        self.django_client = DjangoClient()
        self.login_url = reverse('users:login')

        self.test_user = User.objects.create_user(
            username='detailclientuser',
            email='detailclientuser@example.com',
            password='password123'
        )
        self.test_company = Company.objects.create(name="Detail Client Test Co", owner=self.test_user)

        self.client_instance = Client.objects.create(
            company_account=self.test_company,
            client_name="Detailed Client One",
            email="detailed@example.com",
            phone="555-1234"
        )
        self.detail_url = reverse('clients:detail', kwargs={'client_id': self.client_instance.id})

        # Connexion et setup session
        self.django_client.login(username='detailclientuser@example.com', password='password123')
        session = self.django_client.session
        session['api_auth_token'] = 'faketesttoken_detail123'
        session['active_company_id'] = str(self.test_company.id)
        session['active_company_name'] = self.test_company.name
        session.save()

        # Réponse API mockée pour un détail client réussi
        self.mock_api_detail_success_response = {
            "id": str(self.client_instance.id),
            "client_name": "Detailed Client One",
            "email": "detailed@example.com",
            "phone": "555-1234",
            "address": "123 Detail St",
            "contact_person_name": "Contact D.",
            "contact_person_email": "contactd@example.com",
            "contact_person_phone": "555-0000",
            "notes": "Some notes here.",
            "is_active": True,
            "company_account": str(self.test_company.id),
            "company_account_name": self.test_company.name,
            "created_at": "2023-01-10T10:00:00Z",
            "updated_at": "2023-01-10T11:00:00Z",
        }

    def test_client_detail_view_unauthenticated(self):
        self.django_client.logout()
        response = self.django_client.get(self.detail_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.detail_url}")

    @patch('requests.get')
    def test_client_detail_view_displays_data_from_api(self, mock_api_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_detail_success_response
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_detail.html')
        self.assertIn('client', response.context)
        self.assertEqual(response.context['client']['client_name'], "Detailed Client One")
        self.assertContains(response, "Detailed Client One")
        self.assertContains(response, "detailed@example.com")

        expected_api_url = f"http://localhost:8000/api/v1/clients/{self.client_instance.id}/"
        mock_api_get.assert_called_once_with(
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken_detail123'}
        )

    @patch('requests.get')
    def test_client_detail_view_api_returns_404(self, mock_api_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.detail_url)
        self.assertRedirects(response, reverse('clients:list')) # Redirige vers la liste
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Client non trouvé" in str(m) for m in messages_list))

    @patch('requests.get')
    def test_client_detail_view_api_returns_403_forbidden(self, mock_api_get):
        # Simule le cas où l'API retourne 403 car le client n'appartient pas à la société de l'user
        # (même si notre ViewSet API devrait plutôt retourner 404 dans ce cas via le filtrage du queryset)
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.detail_url)
        self.assertRedirects(response, reverse('clients:list'))
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Vous n'êtes pas autorisé à voir ce client" in str(m) for m in messages_list))


    def test_client_detail_view_no_active_company_in_session(self):
        session = self.django_client.session
        del session['active_company_id']
        session.save()

        response = self.django_client.get(self.detail_url)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))
        # Le message d'avertissement est affiché sur la requête avant redirection.
        # Pour le tester, il faudrait suivre la redirection et vérifier le contexte de la page finale,
        # ou inspecter la réponse avant redirection si possible (plus complexe avec le client de test).

    # Test pour vérifier que le lien "Modifier" et "Retour à la liste" sont présents
    @patch('requests.get')
    def test_client_detail_view_action_links_present(self, mock_api_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_detail_success_response
        mock_api_get.return_value = mock_response

        response = self.django_client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('clients:update', kwargs={'client_id': self.client_instance.id}))
        self.assertContains(response, "Modifier")
        self.assertContains(response, reverse('clients:list'))


class ClientUpdateViewWebTests(TestCase):
    def setUp(self):
        self.django_client = DjangoClient()
        self.login_url = reverse('users:login')

        self.test_user = User.objects.create_user(
            username='updateclientuser',
            email='updateclientuser@example.com',
            password='password123'
        )
        self.test_company = Company.objects.create(name="Update Client Test Co", owner=self.test_user)

        self.client_instance = Client.objects.create(
            company_account=self.test_company,
            client_name="Client To Update",
            email="toupdate@example.com",
        )
        self.update_url = reverse('clients:update', kwargs={'client_id': self.client_instance.id})
        self.detail_url = reverse('clients:detail', kwargs={'client_id': self.client_instance.id})
        self.list_url = reverse('clients:list')

        # Connexion et setup session
        self.django_client.login(username='updateclientuser@example.com', password='password123')
        session = self.django_client.session
        session['api_auth_token'] = 'faketesttoken_update123'
        session['active_company_id'] = str(self.test_company.id)
        session['active_company_name'] = self.test_company.name
        session.save()

        self.client_initial_api_data = { # Ce que l'API GET /client_id/ retournerait
            "id": str(self.client_instance.id),
            "client_name": "Client To Update",
            "email": "toupdate@example.com",
            "phone": "", "address": "", "contact_person_name": "",
            "contact_person_email": "", "contact_person_phone": "",
            "notes": "", "is_active": True,
            "company_account": str(self.test_company.id)
        }
        self.form_update_data = { # Données envoyées par le formulaire POST
            'client_name': 'Client Updated Successfully',
            'email': 'updated@example.com',
            'phone': '111222333',
            'is_active': True,
            # Les autres champs optionnels peuvent être vides ou non envoyés si pas modifiés
        }
        self.mock_api_update_success_response = { # Ce que l'API PUT /client_id/ retournerait
            "id": str(self.client_instance.id),
            "client_name": "Client Updated Successfully",
            "email": "updated@example.com",
            "phone": "111222333",
             "is_active": True,
            # ... autres champs ...
        }

    @patch('requests.get')
    def test_client_update_view_get_displays_form_with_initial_data(self, mock_api_get):
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.client_initial_api_data
        mock_api_get.return_value = mock_response_get

        response = self.django_client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_form.html')
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertIsInstance(form, ClientForm)
        self.assertEqual(form.initial.get('client_name'), self.client_initial_api_data['client_name'])
        self.assertEqual(form.initial.get('email'), self.client_initial_api_data['email'])
        self.assertEqual(response.context['page_title'], f"Modifier le Client : {self.client_initial_api_data['client_name']}")

        expected_api_url = f"http://localhost:8000/api/v1/clients/{self.client_instance.id}/"
        mock_api_get.assert_called_once_with(
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken_update123'}
        )

    @patch('requests.put')
    @patch('requests.get') # Aussi pour le GET initial si la vue redirige vers le détail
    def test_client_update_view_post_success(self, mock_api_get_fordetail, mock_api_put):
        # Mock pour l'appel PUT
        mock_response_put = MagicMock()
        mock_response_put.status_code = 200 # Succès de la mise à jour
        mock_response_put.json.return_value = self.mock_api_update_success_response
        mock_api_put.return_value = mock_response_put

        # Mock pour l'appel GET vers le détail après redirection (non essentiel ici si on ne suit pas la redir)
        # mock_response_get = MagicMock()
        # mock_response_get.status_code = 200
        # mock_response_get.json.return_value = self.mock_api_update_success_response
        # mock_api_get_fordetail.return_value = mock_response_get


        response = self.django_client.post(self.update_url, self.form_update_data)

        self.assertRedirects(response, self.detail_url) # Redirige vers la page de détail
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Client 'Client Updated Successfully' mis à jour" in str(m) for m in messages_list))

        expected_api_url = f"http://localhost:8000/api/v1/clients/{self.client_instance.id}/"
        mock_api_put.assert_called_once_with(
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken_update123'},
            json=self.form_update_data
        )

    @patch('requests.get') # Pour le GET initial du formulaire
    def test_client_update_view_post_form_invalid(self, mock_api_get_initial):
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.client_initial_api_data
        mock_api_get_initial.return_value = mock_response_get

        invalid_data = self.form_update_data.copy()
        invalid_data['client_name'] = '' # Invalide
        response = self.django_client.post(self.update_url, invalid_data)

        self.assertEqual(response.status_code, 200) # Reste sur la page
        self.assertTemplateUsed(response, 'clients/client_form.html')
        self.assertFormError(response, 'form', 'client_name', 'Ce champ est obligatoire.')


    @patch('requests.put')
    @patch('requests.get') # Pour le GET initial du formulaire
    def test_client_update_view_api_validation_error(self, mock_api_get_initial, mock_api_put):
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.client_initial_api_data
        mock_api_get_initial.return_value = mock_response_get

        mock_response_put = MagicMock()
        mock_response_put.status_code = 400
        mock_response_put.json.return_value = {"email": ["Cet email est déjà utilisé par un autre client."]}
        mock_response_put.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_put)
        mock_api_put.return_value = mock_response_put

        response = self.django_client.post(self.update_url, self.form_update_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_form.html')
        self.assertFormError(response, 'form', 'email', "Cet email est déjà utilisé par un autre client.")

    def test_client_update_view_get_other_company_client_fails_or_redirects(self):
        # Créer un client pour une autre société
        other_user = User.objects.create_user(username="otherowner", email="other@owner.com", password="password")
        other_company = Company.objects.create(name="Other Company", owner=other_user)
        other_client = Client.objects.create(company_account=other_company, client_name="Belongs to Other")

        url_for_other_client_update = reverse('clients:update', kwargs={'client_id': other_client.id})

        # self.django_client est loggué comme self.test_user (owner de self.test_company)
        response = self.django_client.get(url_for_other_client_update)
        # La vue devrait rediriger vers la liste si l'API GET retourne 404 (car le client n'est pas à self.test_user)
        self.assertRedirects(response, self.list_url)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Client non trouvé ou non autorisé" in str(m) for m in messages_list))


class ClientDeactivateViewWebTests(TestCase):
    def setUp(self):
        self.django_client = DjangoClient()
        self.login_url = reverse('users:login')
        self.list_url = reverse('clients:list')

        self.test_user = User.objects.create_user(
            username='deactivateclientuser',
            email='deactivateclientuser@example.com',
            password='password123'
        )
        self.test_company = Company.objects.create(name="Deactivate Client Test Co", owner=self.test_user)

        self.active_client = Client.objects.create(
            company_account=self.test_company,
            client_name="Client To Deactivate",
            is_active=True
        )
        self.inactive_client = Client.objects.create(
            company_account=self.test_company,
            client_name="Already Inactive Client",
            is_active=False
        )
        self.deactivate_url_active = reverse('clients:deactivate', kwargs={'client_id': self.active_client.id})
        self.deactivate_url_inactive = reverse('clients:deactivate', kwargs={'client_id': self.inactive_client.id})


        # Connexion et setup session
        self.django_client.login(username='deactivateclientuser@example.com', password='password123')
        session = self.django_client.session
        session['api_auth_token'] = 'faketesttoken_deactivate123'
        session['active_company_id'] = str(self.test_company.id)
        session['active_company_name'] = self.test_company.name
        session.save()

        self.mock_api_get_client_active_response = { "id": str(self.active_client.id), "client_name": "Client To Deactivate", "is_active": True }
        self.mock_api_get_client_inactive_response = { "id": str(self.inactive_client.id), "client_name": "Already Inactive Client", "is_active": False }
        self.mock_api_patch_success_response = { "id": str(self.active_client.id), "client_name": "Client To Deactivate", "is_active": False }

    @patch('requests.get')
    def test_deactivate_view_get_displays_confirmation(self, mock_api_get):
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.mock_api_get_client_active_response
        mock_api_get.return_value = mock_response_get

        response = self.django_client.get(self.deactivate_url_active)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/client_confirm_deactivate.html')
        self.assertContains(response, "Confirmer la Désactivation")
        self.assertContains(response, self.active_client.client_name)
        mock_api_get.assert_called_once()

    @patch('requests.get') # Pour le GET initial de la page de confirmation
    @patch('requests.patch') # Pour le POST de désactivation
    def test_deactivate_view_post_success(self, mock_api_patch, mock_api_get_confirm):
        # Mock pour le GET de la page de confirmation
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.mock_api_get_client_active_response # Client est actif
        mock_api_get_confirm.return_value = mock_response_get

        # Mock pour l'appel PATCH de l'API
        mock_response_patch = MagicMock()
        mock_response_patch.status_code = 200 # Succès de la mise à jour partielle
        mock_response_patch.json.return_value = self.mock_api_patch_success_response
        mock_api_patch.return_value = mock_response_patch

        response = self.django_client.post(self.deactivate_url_active)
        self.assertRedirects(response, self.list_url)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any(f"Le client '{self.active_client.client_name}' a été désactivé avec succès." in str(m) for m in messages_list))

        expected_api_url = f"http://localhost:8000/api/v1/clients/{self.active_client.id}/"
        mock_api_patch.assert_called_once_with(
            expected_api_url,
            headers={'Authorization': f'Token faketesttoken_deactivate123'},
            json={'is_active': False}
        )

    @patch('requests.get')
    def test_deactivate_view_get_for_already_inactive_client_redirects(self, mock_api_get):
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.mock_api_get_client_inactive_response # Client est déjà inactif
        mock_api_get.return_value = mock_response_get

        response = self.django_client.get(self.deactivate_url_inactive)
        detail_url_inactive = reverse('clients:detail', kwargs={'client_id': self.inactive_client.id})
        self.assertRedirects(response, detail_url_inactive)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any(f"Le client '{self.inactive_client.client_name}' est déjà inactif." in str(m) for m in messages_list))


    @patch('requests.get') # Pour le GET de confirmation
    @patch('requests.patch') # Pour le POST
    def test_deactivate_view_api_patch_fails(self, mock_api_patch, mock_api_get_confirm):
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = self.mock_api_get_client_active_response
        mock_api_get_confirm.return_value = mock_response_get

        mock_response_patch = MagicMock()
        mock_response_patch.status_code = 400 # Erreur de l'API
        mock_response_patch.json.return_value = {"detail": "Erreur API lors de la désactivation."}
        mock_response_patch.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_patch)
        mock_api_patch.return_value = mock_response_patch

        response = self.django_client.post(self.deactivate_url_active)
        self.assertRedirects(response, self.list_url) # Redirige toujours vers la liste
        messages_list = list(get_messages(response.wsgi_request))
        # Le message exact dépend de la gestion d'erreur dans la vue
        self.assertTrue(any("Erreur API" in str(m) for m in messages_list))

    def test_deactivate_view_unauthenticated(self):
        self.django_client.logout()
        response_get = self.django_client.get(self.deactivate_url_active)
        self.assertRedirects(response_get, f"{self.login_url}?next={self.deactivate_url_active}")
        response_post = self.django_client.post(self.deactivate_url_active)
        self.assertRedirects(response_post, f"{self.login_url}?next={self.deactivate_url_active}")

    def test_deactivate_view_no_active_company(self):
        session = self.django_client.session
        del session['active_company_id']
        session.save()

        response = self.django_client.get(self.deactivate_url_active)
        self.assertRedirects(response, reverse(settings.LOGIN_REDIRECT_URL))
