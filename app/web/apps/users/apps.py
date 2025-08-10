from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users' # Important pour que Django trouve l'app dans le dossier apps/
    label = 'users' # Label unique pour l'application
