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
