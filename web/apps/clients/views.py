from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests # Pour les appels API

# API_BASE_URL = getattr(settings, "API_BASE_URL", "http://localhost:8000/api/v1")
# Déjà défini dans apps.users.views, mais il serait mieux de le centraliser ou de le passer via le contexte/settings Django
# Pour l'instant, je le re-définis ici pour la clarté de ce module.
# Une meilleure approche serait un helper ou un service pour faire les appels API.
API_BASE_URL = "http://localhost:8000/api/v1" # Supposons qu'il soit accessible ainsi en dev

@login_required
def client_list_view(request):
    api_auth_token = request.session.get('api_auth_token')
    active_company_id = request.session.get('active_company_id')

    if not api_auth_token:
        messages.error(request, "Erreur d'authentification API. Veuillez vous reconnecter.")
        return redirect('users:login') # Assurez-vous que cette URL est correcte

    if not active_company_id:
        messages.warning(request, "Veuillez sélectionner une société active pour voir les clients.")
        # Rediriger vers une page de sélection de société si elle existe, sinon dashboard ou profil.
        # Pour l'instant, on redirige vers le dashboard (qui devrait idéalement gérer ça).
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main'))

    headers = {'Authorization': f'Token {api_auth_token}'}

    # Préparer les paramètres pour l'API (pagination, filtres)
    params = {
        'company_account_id': active_company_id, # Crucial pour le multi-tenant
        'page': request.GET.get('page', 1),
    }
    search_query = request.GET.get('search_query', '')
    status_filter = request.GET.get('is_active', '')

    if search_query:
        params['search'] = search_query # L'API ClientViewSet doit supporter ce paramètre
    if status_filter in ['true', 'false']:
        params['is_active'] = status_filter # L'API ClientViewSet doit supporter ce paramètre

    clients_api_url = f"{API_BASE_URL}/clients/"

    # Pour la pagination avec filtres conservés
    current_query_params = request.GET.copy()

    context = {
        'page_title': 'Liste des Clients',
        'search_query': search_query,
        'status_filter': status_filter,
        'clients_data': None, # Initialiser
        'current_query_params': current_query_params.urlencode() # Pour les liens de pagination
    }

    try:
        response = requests.get(clients_api_url, headers=headers, params=params)
        response.raise_for_status() # Lèvera une exception pour 4xx/5xx

        clients_data = response.json() # DRF retourne une structure avec 'count', 'next', 'previous', 'results'
        context['clients_data'] = clients_data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401: # Non autorisé par l'API
            messages.error(request, "Session API invalide. Veuillez vous reconnecter.")
            # Potentiellement, déconnecter l'utilisateur Django aussi et supprimer le token de session
            # django_logout(request)
            # if 'api_auth_token' in request.session: del request.session['api_auth_token']
            return redirect('users:login')
        elif e.response.status_code == 403: # Interdit (ex: mauvaise company_id ou droits insuffisants)
             messages.error(request, "Vous n'êtes pas autorisé à voir les clients de cette société.")
        else:
            messages.error(request, f"Erreur lors de la récupération des clients (API Error {e.response.status_code}).")
    except requests.exceptions.RequestException:
        messages.error(request, "Erreur de communication avec le service des clients.")
    except ValueError: # Erreur de décodage JSON
        messages.error(request, "Réponse invalide du service des clients.")

    # Gérer les requêtes HTMX pour le rechargement partiel
    if request.htmx:
        template_name = 'clients/partials/_client_list_table.html' # Template partiel pour la table
    else:
        template_name = 'clients/client_list.html' # Template complet

    return render(request, template_name, context)

from .forms import ClientForm # Importer ClientForm

@login_required
def client_create_view(request):
    api_auth_token = request.session.get('api_auth_token')
    active_company_id = request.session.get('active_company_id')
    active_company_name = request.session.get('active_company_name', 'N/A')

    if not api_auth_token:
        messages.error(request, "Erreur d'authentification API. Veuillez vous reconnecter.")
        return redirect('users:login')

    if not active_company_id:
        messages.warning(request, "Veuillez sélectionner une société active pour ajouter un client.")
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main'))

    headers = {'Authorization': f'Token {api_auth_token}'}
    form = ClientForm(request.POST or None) # Initialiser avec request.POST si method est POST, sinon None

    if request.method == 'POST':
        if form.is_valid():
            api_data = form.cleaned_data.copy()
            # La company_account sera gérée par le ViewSet API basé sur l'utilisateur authentifié
            # et sa société active. On n'a pas besoin de la passer explicitement ici si le ViewSet
            # est bien configuré pour la déduire de request.user ou d'une company_id passée en paramètre
            # que la permission validerait.
            # Pour le moment, on suppose que le ViewSet ClientViewSet.perform_create s'en charge.

            create_api_url = f"{API_BASE_URL}/clients/" # URL de l'endpoint de création de l'API

            try:
                # Utiliser json= pour envoyer les données en JSON pour POST/PUT/PATCH avec DRF
                response = requests.post(create_api_url, headers=headers, json=api_data)
                response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP 4xx/5xx

                created_client_data = response.json() # Récupérer les données du client créé depuis l'API
                messages.success(request, f"Client '{created_client_data.get('client_name', '')}' créé avec succès.")
                # Rediriger vers la liste des clients ou le détail du client nouvellement créé
                return redirect('clients:list') # Assurez-vous que 'clients:list' est le nom d'URL correct

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400: # Erreur de validation de l'API
                    error_data = e.response.json()
                    # Parcourir les erreurs retournées par l'API et les ajouter au formulaire Django
                    for field, errors in error_data.items():
                        if field in form.fields: # Si l'erreur de l'API concerne un champ du formulaire
                            for error in errors if isinstance(errors, list) else [errors]:
                                form.add_error(field, error)
                        # Gérer les erreurs non liées à un champ (non_field_errors de DRF)
                        # ou les erreurs de champs API qui n'existent pas dans le form Django
                        elif field == 'detail' or field == 'non_field_errors':
                             for error in errors if isinstance(errors, list) else [errors]:
                                messages.error(request, error) # Afficher comme message global
                        else: # Erreur de champ API non mappée directement au formulaire
                            for error in errors if isinstance(errors, list) else [errors]:
                                messages.error(request, f"Erreur API pour '{field}': {error}")
                elif e.response.status_code == 401: # Non autorisé par l'API (token invalide/expiré)
                     messages.error(request, "Session API invalide ou expirée. Veuillez vous reconnecter.")
                     return redirect('users:login')
                elif e.response.status_code == 403: # Interdit (droits insuffisants)
                     messages.error(request, "Action non autorisée par l'API pour créer ce client.")
                else: # Autre erreur HTTP de l'API
                    messages.error(request, f"Une erreur s'est produite lors de la création du client (Erreur API {e.response.status_code}).")
            except requests.exceptions.RequestException: # Erreur de connexion à l'API
                messages.error(request, "Erreur de communication avec le service des clients. Veuillez réessayer plus tard.")
            except ValueError: # Erreur de décodage JSON de la réponse de l'API
                messages.error(request, "Réponse invalide ou mal formatée reçue du service des clients.")
        else: # Le formulaire Django n'est pas valide (validation côté client/Django avant appel API)
            messages.warning(request, "Veuillez corriger les erreurs indiquées dans le formulaire.")

    context = {
        'form': form,
        'page_title': 'Ajouter un Nouveau Client',
        'active_company_name': active_company_name, # Pour l'affichage dans le template
        'submit_button_text': 'Enregistrer le Client' # Texte pour le bouton de soumission
    }
    return render(request, 'clients/client_form.html', context)


@login_required
def client_detail_view(request, client_id): # client_id est passé par l'URL
    api_auth_token = request.session.get('api_auth_token')
    active_company_id = request.session.get('active_company_id') # Utilisé pour le contexte, l'API gère la permission
    active_company_name = request.session.get('active_company_name', 'N/A')

    if not api_auth_token:
        messages.error(request, "Erreur d'authentification API. Veuillez vous reconnecter.")
        return redirect('users:login')

    # Bien que l'API ClientViewSet doive filtrer par company, avoir active_company_id ici
    # est utile pour le contexte ou si on voulait ajouter une vérification supplémentaire (redondante si API bien faite).
    if not active_company_id:
        messages.warning(request, "Veuillez sélectionner une société active.")
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main'))

    headers = {'Authorization': f'Token {api_auth_token}'}
    client_detail_api_url = f"{API_BASE_URL}/clients/{client_id}/"

    client_data = None
    try:
        response = requests.get(client_detail_api_url, headers=headers)
        response.raise_for_status()
        client_data = response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            messages.error(request, "Client non trouvé ou vous n'avez pas la permission de le voir.")
            return redirect('clients:list') # Rediriger vers la liste
        elif e.response.status_code == 401:
             messages.error(request, "Session API invalide. Veuillez vous reconnecter.")
             return redirect('users:login')
        elif e.response.status_code == 403: # Normalement géré par le 404 du ViewSet si le queryset ne trouve rien
             messages.error(request, "Vous n'êtes pas autorisé à voir ce client.")
             return redirect('clients:list')
        else:
            messages.error(request, f"Erreur lors de la récupération du client (API Error {e.response.status_code}).")
            return redirect('clients:list') # Ou une page d'erreur générique
    except requests.exceptions.RequestException:
        messages.error(request, "Erreur de communication avec le service des clients.")
        return redirect('clients:list')
    except ValueError: # Erreur de décodage JSON
        messages.error(request, "Réponse invalide du service des clients.")
        return redirect('clients:list')

    context = {
        'client': client_data,
        'page_title': f"Détails du Client : {client_data.get('client_name', '') if client_data else 'N/A'}",
        'active_company_name': active_company_name,
    }
    return render(request, 'clients/client_detail.html', context)


@login_required
def client_update_view(request, client_id):
    api_auth_token = request.session.get('api_auth_token')
    active_company_id = request.session.get('active_company_id')
    active_company_name = request.session.get('active_company_name', 'N/A')

    if not api_auth_token:
        messages.error(request, "Erreur d'authentification API. Veuillez vous reconnecter.")
        return redirect('users:login')

    if not active_company_id: # Important pour le contexte, même si l'API vérifie la propriété
        messages.warning(request, "Veuillez sélectionner une société active.")
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main'))

    headers = {'Authorization': f'Token {api_auth_token}'}
    client_api_url = f"{API_BASE_URL}/clients/{client_id}/"

    # Récupérer les données initiales du client pour pré-remplir le formulaire en GET
    if request.method == 'GET':
        try:
            response_get = requests.get(client_api_url, headers=headers)
            response_get.raise_for_status()
            client_initial_data = response_get.json()
            # Le ClientForm n'est pas un ModelForm, donc on passe les initiales.
            # Il faut s'assurer que les clés de client_initial_data correspondent aux champs du ClientForm.
            form = ClientForm(initial=client_initial_data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                messages.error(request, "Client non trouvé ou non autorisé.")
            else:
                messages.error(request, f"Erreur API ({e.response.status_code}) lors de la récupération du client.")
            return redirect('clients:list')
        except requests.exceptions.RequestException:
            messages.error(request, "Erreur de communication pour récupérer les détails du client.")
            return redirect('clients:list')

    elif request.method == 'POST':
        form = ClientForm(request.POST) # Pas d'instance pour un forms.Form simple
        if form.is_valid():
            api_data = form.cleaned_data.copy()
            # La company_account ne devrait pas être modifiable via ce formulaire directement
            # si elle est gérée par l'appartenance à l'utilisateur.
            # L'API (PUT) s'attend à recevoir tous les champs requis pour une mise à jour complète.
            # Notre ClientSerializer est configuré avec company_account en write_only=True, required=False
            # car le ViewSet le gère. Pour un PUT via l'API, le ViewSet va utiliser l'instance existante.
            # Donc, ne pas envoyer company_account ici est correct si l'API ne l'attend pas pour un PUT.
            # Si l'API l'attendait, il faudrait le récupérer de l'instance initiale.

            try:
                response_put = requests.put(client_api_url, headers=headers, json=api_data)
                response_put.raise_for_status()

                updated_client_data = response_put.json()
                messages.success(request, f"Client '{updated_client_data.get('client_name', '')}' mis à jour avec succès.")
                return redirect('clients:detail', client_id=client_id) # Rediriger vers le détail

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    error_data = e.response.json()
                    for field, errors in error_data.items():
                        if field in form.fields:
                            for error in errors if isinstance(errors, list) else [errors]:
                                form.add_error(field, error)
                        elif field == 'detail' or field == 'non_field_errors':
                             for error in errors if isinstance(errors, list) else [errors]:
                                messages.error(request, error)
                        else:
                            for error in errors if isinstance(errors, list) else [errors]:
                                messages.error(request, f"Erreur API pour '{field}': {error}")
                elif e.response.status_code == 404:
                    messages.error(request, "Client non trouvé pour la mise à jour.")
                    return redirect('clients:list')
                # Autres erreurs (401, 403) gérées par les redirections au début ou par l'API elle-même.
                else:
                    messages.error(request, f"Erreur API ({e.response.status_code}) lors de la mise à jour du client.")
            except requests.exceptions.RequestException:
                messages.error(request, "Erreur de communication lors de la mise à jour du client.")
            except ValueError:
                 messages.error(request, "Réponse invalide du service lors de la mise à jour.")
        else:
            messages.warning(request, "Veuillez corriger les erreurs dans le formulaire.")
    else: # Méthode non GET ou POST (improbable ici)
        form = ClientForm() # Devrait déjà être initialisé par le GET

    context = {
        'form': form,
        'page_title': f"Modifier le Client : {client_initial_data.get('client_name', '') if request.method == 'GET' and 'client_initial_data' in locals() else 'Client'}",
        'active_company_name': active_company_name,
        'submit_button_text': 'Enregistrer les Modifications',
        'client_id': client_id # Pour l'URL du formulaire si besoin (pas pour POST car déjà dans l'URL)
    }
    return render(request, 'clients/client_form.html', context)


@login_required
def client_deactivate_view(request, client_id):
    api_auth_token = request.session.get('api_auth_token')
    active_company_id = request.session.get('active_company_id') # Vérification de la société active
    active_company_name = request.session.get('active_company_name', 'N/A')

    if not api_auth_token:
        messages.error(request, "Erreur d'authentification API. Veuillez vous reconnecter.")
        return redirect('users:login')

    if not active_company_id:
        messages.warning(request, "Veuillez sélectionner une société active.")
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main'))

    headers = {'Authorization': f'Token {api_auth_token}'}
    client_api_url = f"{API_BASE_URL}/clients/{client_id}/" # Endpoint de détail/update/patch

    # Récupérer les infos du client pour la page de confirmation (en GET)
    client_data = None
    if request.method == 'GET':
        try:
            response_get = requests.get(client_api_url, headers=headers)
            response_get.raise_for_status()
            client_data = response_get.json()
            if not client_data.get('is_active', True): # Si déjà inactif
                messages.info(request, f"Le client '{client_data.get('client_name')}' est déjà inactif.")
                return redirect('clients:detail', client_id=client_id)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                messages.error(request, "Client non trouvé ou non autorisé.")
            else:
                messages.error(request, f"Erreur API ({e.response.status_code}) lors de la récupération du client pour désactivation.")
            return redirect('clients:list')
        except requests.exceptions.RequestException:
            messages.error(request, "Erreur de communication pour récupérer les détails du client.")
            return redirect('clients:list')
        except ValueError:
            messages.error(request, "Réponse invalide du service client.")
            return redirect('clients:list')


    if request.method == 'POST':
        try:
            payload = {'is_active': False}
            response_patch = requests.patch(client_api_url, headers=headers, json=payload)
            response_patch.raise_for_status()

            # Récupérer le nom du client depuis la réponse PATCH ou refaire un GET si nécessaire
            # Pour simplifier, on peut utiliser le nom passé en session ou un nom générique.
            # Idéalement, le nom est dans client_data si on vient du GET de confirmation.
            client_name_display = client_data.get('client_name', 'Le client') if client_data else 'Le client'
            if response_patch.status_code == 200: # OK pour PATCH
                 client_name_display = response_patch.json().get('client_name', client_name_display)

            messages.success(request, f"Le client '{client_name_display}' a été désactivé avec succès.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                messages.error(request, "Client non trouvé ou non autorisé pour la désactivation.")
            elif e.response.status_code == 400:
                 error_data = e.response.json()
                 for field, errors in error_data.items():
                     for error in errors if isinstance(errors, list) else [errors]:
                        messages.error(request, f"Erreur API ({field}): {error}")
            else:
                messages.error(request, f"Erreur API ({e.response.status_code}) lors de la désactivation du client.")
        except requests.exceptions.RequestException:
            messages.error(request, "Erreur de communication lors de la désactivation du client.")
        except ValueError:
            messages.error(request, "Réponse invalide du service lors de la désactivation.")

        return redirect('clients:list') # Toujours rediriger après un POST

    # Contexte pour la page de confirmation (GET)
    context = {
        'client': client_data, # client_data peut être None si le GET initial échoue, le template doit gérer ça
        'page_title': f"Désactiver le Client : {client_data.get('client_name', '') if client_data else 'Client'}",
        'active_company_name': active_company_name,
    }
    return render(request, 'clients/client_confirm_deactivate.html', context)
