from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import views_api # Assuming your API views are in views_api.py or similar

# router = DefaultRouter()
# router.register(r'profile', views_api.UserProfileViewSet, basename='userprofile') # Example

app_name = 'users_api'

urlpatterns = [
    # path('', include(router.urls)), # Example
    # path('register/', views_api.UserRegistrationView.as_view(), name='register'), # Example
    # path('login/', views_api.CustomAuthToken.as_view(), name='login'), # Example
]
