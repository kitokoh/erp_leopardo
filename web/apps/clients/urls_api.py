from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api # Assurez-vous que views_api.py contient ClientViewSet

router = DefaultRouter()
router.register(r'', views_api.ClientViewSet, basename='client')
# Le r'' signifie que les URLs seront /api/v1/clients/ (pour la liste/création)
# et /api/v1/clients/{pk}/ (pour détail/màj/suppression)


app_name = 'clients_api'

urlpatterns = [
    path('', include(router.urls)),

]
