from django.urls import path
from . import views # S'assurer que views.py contient client_list_view

app_name = 'clients'

urlpatterns = [
    path('', views.client_list_view, name='list'),
    # path('add/', views.client_create_view, name='create'), # Sera ajouté plus tard
    # path('<uuid:pk>/', views.client_detail_view, name='detail'), # Sera ajouté plus tard
    # path('<uuid:pk>/edit/', views.client_update_view, name='update'), # Sera ajouté plus tard
]
