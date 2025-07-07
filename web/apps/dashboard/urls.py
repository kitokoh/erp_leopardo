from django.urls import path
from . import views # S'assurer que views.py contient dashboard_view


app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='main'),

]
