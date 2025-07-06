from django.urls import path
from . import views # Assurez-vous que views.py contient les vues web

app_name = 'users' # Ce sera utilisé comme namespace, ex: {% url 'users:login' %}

urlpatterns = [
    path('register/', views.user_register_view, name='register'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    # path('profile/', views.user_profile_view, name='profile'), # À ajouter quand la vue profil sera prête
    # Ajouter ici les URLs pour password_change, password_reset, etc. plus tard

]
