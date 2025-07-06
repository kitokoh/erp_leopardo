from django.shortcuts import render, redirect
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib import messages
from django.conf import settings # Pour accéder à l'URL de l'API si besoin
from django.urls import reverse_lazy, reverse
import requests # Pour faire des appels à notre propre API DRF

from .forms import UserRegistrationForm, UserLoginForm # , UserProfileUpdateForm

# Il est préférable de stocker l'URL de base de l'API dans settings.py
API_BASE_URL = getattr(settings, "API_BASE_URL", "http://localhost:8000/api/v1") # Fallback pour dev local

def user_register_view(request):
    if request.user.is_authenticated:
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main')) # Remplacer par la vraie URL du dashboard

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Préparer les données pour l'API d'inscription
            api_data = {
                'username': form.cleaned_data.get('username'),
                'email': form.cleaned_data.get('email'),
                'password': form.cleaned_data.get('password'),
                'password2': form.cleaned_data.get('password2'),
                'first_name': form.cleaned_data.get('first_name'),
                'last_name': form.cleaned_data.get('last_name'),
                'company_name': form.cleaned_data.get('company_name')
            }

            register_api_url = f"{API_BASE_URL}/users/register/" # Construire l'URL de l'API

            try:
                response = requests.post(register_api_url, data=api_data)
                response.raise_for_status() # Lèvera une exception pour les codes 4xx/5xx

                api_response_data = response.json()

                # Si l'inscription API réussit, connecter l'utilisateur dans Django
                # Pour cela, il faut récupérer l'utilisateur créé. L'API retourne les infos user.
                # On pourrait utiliser authenticate() avec les identifiants fournis,
                # ou faire confiance à l'API et connecter l'utilisateur si l'API a réussi.
                # Utilisons authenticate pour être propre :
                user = authenticate(request, username=api_data['email'], password=api_data['password'])

                if user and user.is_active: # S'assurer que l'utilisateur est bien actif
                    django_login(request, user)

                    # Stocker le token API dans la session de l'utilisateur
                    # pour que le backend Django puisse faire des appels API authentifiés si nécessaire
                    if 'token' in api_response_data:
                        request.session['api_auth_token'] = api_response_data['token']

                    # Stocker l'ID de la société active (celle créée par défaut)
                    if 'default_company_id' in api_response_data and api_response_data['default_company_id']:
                         request.session['active_company_id'] = str(api_response_data['default_company_id'])
                         # On pourrait aussi stocker le nom pour l'affichage
                         # active_company = Company.objects.get(id=api_response_data['default_company_id'])
                         # request.session['active_company_name'] = active_company.name


                    messages.success(request, "Inscription réussie ! Vous êtes maintenant connecté.")
                    return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main')) # Remplacer
                else:
                    # Cas étrange où l'API a réussi mais l'authentification Django échoue
                    messages.error(request, "Erreur lors de la connexion après inscription. Veuillez réessayer.")

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400: # Erreur de validation de l'API
                    error_data = e.response.json()
                    for field, errors in error_data.items():
                        for error in errors if isinstance(errors, list) else [errors]:
                            if field == 'non_field_errors':
                                messages.error(request, error)
                            else:
                                form.add_error(field if field in form.fields else None, error)
                else:
                    messages.error(request, f"Une erreur s'est produite lors de l'inscription (API Error {e.response.status_code}). Veuillez réessayer.")
            except requests.exceptions.RequestException:
                messages.error(request, "Erreur de communication avec le service d'authentification. Veuillez réessayer plus tard.")
            except Exception: # Autre exception
                messages.error(request, "Une erreur inattendue s'est produite. Veuillez réessayer.")
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form, 'page_title': "Inscription"})


def user_login_view(request):
    if request.user.is_authenticated:
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main')) # Remplacer

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST) # UserLoginForm hérite de AuthenticationForm
        if form.is_valid():
            # Les données sont validées par AuthenticationForm, on peut récupérer l'utilisateur
            user = form.get_user()

            # Appeler notre API de login pour obtenir le token DRF
            login_api_url = f"{API_BASE_URL}/users/login/"
            api_data = {'email': user.email, 'password': request.POST.get('password')} # Utiliser l'email de l'user authentifié

            try:
                response = requests.post(login_api_url, data=api_data)
                response.raise_for_status()
                api_response_data = response.json()

                # Connecter l'utilisateur dans la session Django
                django_login(request, user)

                # Stocker le token API et la société active
                if 'token' in api_response_data:
                    request.session['api_auth_token'] = api_response_data['token']
                if 'active_company_id' in api_response_data and api_response_data['active_company_id']:
                    request.session['active_company_id'] = str(api_response_data['active_company_id'])
                    if 'active_company_name' in api_response_data: # Stocker aussi le nom pour affichage
                        request.session['active_company_name'] = api_response_data['active_company_name']


                messages.success(request, f"Bienvenue, {user.get_full_name() or user.username} !")

                # Rediriger vers la page 'next' si elle existe, sinon vers le dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', 'dashboard:main')) # Remplacer

            except requests.exceptions.HTTPError as e:
                # L'API de login retourne 400 si les identifiants sont mauvais,
                # mais AuthenticationForm devrait déjà avoir attrapé ça.
                # Ceci est plus pour des erreurs serveur de l'API.
                messages.error(request, f"Erreur de connexion via l'API (Code: {e.response.status_code}). Veuillez réessayer.")
            except requests.exceptions.RequestException:
                messages.error(request, "Erreur de communication avec le service de connexion. Veuillez réessayer plus tard.")
            except Exception:
                 messages.error(request, "Une erreur inattendue s'est produite lors de la connexion.")

        else: # Le formulaire Django AuthenticationForm n'est pas valide
            # Les messages d'erreur du formulaire sont gérés par le template
            pass
            # messages.error(request, "Email ou mot de passe incorrect.") # Ou form.errors
    else:
        form = UserLoginForm(request)

    return render(request, 'users/login.html', {'form': form, 'page_title': "Connexion"})


def user_logout_view(request):
    # Optionnel: Invalider le token API côté serveur si cette logique est implémentée
    # api_auth_token = request.session.get('api_auth_token')
    # if api_auth_token:
    #     try:
    #         logout_api_url = f"{API_BASE_URL}/users/logout/" # Endpoint à créer
    #         requests.post(logout_api_url, headers={'Authorization': f'Token {api_auth_token}'})
    #     except requests.exceptions.RequestException:
    #         # Gérer l'échec de l'appel API de déconnexion (ne pas bloquer la déconnexion Django)
    #         pass

    django_logout(request) # Termine la session Django

    # Nettoyer la session des données spécifiques à notre application
    if 'api_auth_token' in request.session:
        del request.session['api_auth_token']
    if 'active_company_id' in request.session:
        del request.session['active_company_id']
    if 'active_company_name' in request.session:
        del request.session['active_company_name']

    messages.info(request, "Vous avez été déconnecté.")
    return redirect(getattr(settings, 'LOGOUT_REDIRECT_URL', 'users:login')) # Remplacer 'users:login' par la vraie URL


# Vue pour le profil utilisateur (à compléter)
# from django.contrib.auth.decorators import login_required
# @login_required
# def user_profile_view(request):
#     if request.method == 'POST':
#         form = UserProfileUpdateForm(request.POST, instance=request.user)
#         if form.is_valid():
#             # Préparer les données pour l'API /users/me/ (PUT ou PATCH)
#             # ... appel API ...
#             # messages.success(request, "Profil mis à jour.")
#             # form.save() # Si on ne passe pas par l'API pour la màj simple du User model
#             pass
#     else:
#         form = UserProfileUpdateForm(instance=request.user)
#     return render(request, 'users/profile.html', {'form': form, 'page_title': "Mon Profil"})

