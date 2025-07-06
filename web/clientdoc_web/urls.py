"""
URL configuration for clientdoc_web project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API V1
    path('api/v1/users/', include('apps.users.urls_api')),
    # path('api/v1/clients/', include('apps.clients.urls_api')),
    # path('api/v1/products/', include('apps.products.urls_api')),
    # path('api/v1/documents/', include('apps.documents.urls_api')),

    # Frontend App URLs
    # path('', include('apps.dashboard.urls')), # Dashboard typically at root
    # path('auth/', include('apps.users.urls')), # For login, register, profile web pages
    # path('clients/', include('apps.clients.urls')),
    # path('products/', include('apps.products.urls')),
    # path('documents/', include('apps.documents.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Usually not needed with WhiteNoise for dev if correctly set up
