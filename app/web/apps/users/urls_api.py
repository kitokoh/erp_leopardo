from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    UserRegistrationView,
    CustomAuthTokenView,
    UserDetailView,
    CompanyViewSet,
    # PasswordChangeView, # Décommenter si implémenté
)

# Le router gère automatiquement la création des URLs pour les ViewSets (liste, détail, etc.)
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
# Ex: /api/v1/users/companies/
#     /api/v1/users/companies/{company_pk}/

app_name = 'users_api' # Important pour le namespacing des URLs (ex: reverse('users_api:register'))

urlpatterns = [
    # URLs pour l'authentification et la gestion du profil utilisateur
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomAuthTokenView.as_view(), name='login'),
    path('me/', UserDetailView.as_view(), name='me'), # Pour GET (voir profil) et PUT/PATCH (modifier profil)

    # URLs pour le changement de mot de passe (si implémenté)
    # path('password/change/', PasswordChangeView.as_view(), name='password_change'),

    # Inclure les URLs générées par le router pour CompanyViewSet
    # Celles-ci seront préfixées par le path défini dans le urls.py principal du projet
    # (ex: si le urls.py principal inclut `path('api/v1/users/', include('apps.users.urls_api'))`,
    # alors les URLs du router commenceront par `/api/v1/users/`)
    # Pour CompanyViewSet, on le met à la racine de cet `urls_api.py`
    # donc, il sera accessible via `/api/v1/users/companies/`
    path('', include(router.urls)),
]

# URLs pour la réinitialisation de mot de passe (si on n'utilise pas dj_rest_auth)
# Elles sont souvent laissées à Django pour rendre des templates HTML ou nécessitent des vues plus complexes.
# Exemple si on utilisait les vues Django par défaut pour le reset (qui rendent des templates):
# from django.contrib.auth import views as auth_views
# urlpatterns += [
#     path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
#     path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
#     path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
#     path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
# ]

