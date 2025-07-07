from django.urls import path
from . import views # S'assurer que views.py contient client_list_view

app_name = 'clients'

urlpatterns = [
    path('', views.client_list_view, name='list'),
    path('add/', views.client_create_view, name='create'),
    path('<uuid:client_id>/', views.client_detail_view, name='detail'),
    path('<uuid:client_id>/edit/', views.client_update_view, name='update'),
]
