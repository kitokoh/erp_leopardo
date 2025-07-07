from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_api # Assurez-vous que views_api.py contient les ViewSets

router = DefaultRouter()
router.register(r'categories', views_api.ProductCategoryViewSet, basename='productcategory')
router.register(r'', views_api.ProductViewSet, basename='product')
# Pour ProductViewSet, le r'' signifie que les URLs seront:
# /api/v1/products/ (liste/création de produits)
# /api/v1/products/{pk}/ (détail/màj/suppression de produit)
# /api/v1/products/categories/ (liste/création de catégories)
# /api/v1/products/categories/{pk}/ (détail/màj/suppression de catégorie)

app_name = 'products_api'

urlpatterns = [
    path('', include(router.urls)),
]
