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


# Les vues pour create, detail, update, delete seront ajoutées ici plus tard.
# Exemple pour client_create_view:
# from .forms import ClientForm
# @login_required
# def client_create_view(request):
#     api_auth_token = request.session.get('api_auth_token')
#     active_company_id = request.session.get('active_company_id')
#     # ... (vérifications token et company_id) ...
#     headers = {'Authorization': f'Token {api_auth_token}'}
#     form = ClientForm(request.POST or None)
#     if request.method == 'POST' and form.is_valid():
#         api_data = form.cleaned_data.copy() # Adapter les champs si nécessaire
#         api_data['company_account'] = active_company_id # Assigner la société active
#         create_api_url = f"{API_BASE_URL}/clients/"
#         try:
#             response = requests.post(create_api_url, headers=headers, json=api_data) # Utiliser json= pour POST/PUT/PATCH
#             response.raise_for_status()
#             messages.success(request, "Client créé avec succès.")
#             return redirect('clients:list') # Assurez-vous que cette URL est correcte
#         except requests.exceptions.HTTPError as e:
#             # Gérer les erreurs de l'API et les ajouter au formulaire ou aux messages
#             # ...
#         except requests.exceptions.RequestException:
#             # ...
#     context = {'form': form, 'page_title': 'Ajouter un Client'}
#     return render(request, 'clients/client_form.html', context)
