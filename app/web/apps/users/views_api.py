from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken # Vue de base pour le login
from .serializers import UserRegistrationSerializer, UserSerializer, CompanySerializer
from .models import Company
from .permissions import IsOwnerOfCompany, CanManageObjectBasedOnCompany # Nos permissions personnalisées

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """
    Vue pour l'inscription de nouveaux utilisateurs.
    Accessible à tous (AllowAny).
    Crée un User et une Company par défaut, puis retourne les infos User et un Token.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Tout le monde peut s'inscrire

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save() # Le .save() du serializer gère la création User + Company

        token, created = Token.objects.get_or_create(user=user)

        # Récupérer la société par défaut créée pour cet utilisateur
        # Normalement, l'utilisateur n'aura qu'une seule société juste après l'inscription
        default_company = Company.objects.filter(owner=user).first() # Devrait exister

        user_data = UserSerializer(user, context={'request': request}).data
        # On pourrait vouloir enrichir user_data avec des infos de la société active ou du token
        # pour le client frontend, mais le token est généralement suffisant pour la suite.

        return Response(
            {
                "message": "Inscription réussie.",
                "user": user_data,
                "token": token.key,
                "default_company_id": default_company.id if default_company else None
            },
            status=status.HTTP_201_CREATED
        )


class CustomAuthTokenView(ObtainAuthToken):
    """
    Vue pour la connexion des utilisateurs.
    Hérite de ObtainAuthToken de DRF et personnalise la réponse.
    """
    # serializer_class = AuthTokenSerializer # Par défaut, si on ne le surcharge pas

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Valide username & password
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        # Récupérer la première société de l'utilisateur (ou la société "active" si cette logique est en place)
        # Pour l'instant, on prend la première. Ce sera important pour le frontend de savoir
        # dans quel contexte de société l'utilisateur se connecte.
        active_company = Company.objects.filter(owner=user).order_by('created_at').first()

        user_data = UserSerializer(user, context={'request': request}).data

        return Response({
            'token': token.key,
            'user': user_data,
            'active_company_id': active_company.id if active_company else None,
            'active_company_name': active_company.name if active_company else None,
            # On peut ajouter d'autres informations utiles ici, comme les permissions/rôles de base
        })


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour les informations de l'utilisateur connecté ('me').
    L'utilisateur ne peut accéder qu'à son propre profil.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # S'assure que l'utilisateur ne peut récupérer/modifier que son propre objet User.
        return self.request.user

    def update(self, request, *args, **kwargs):
        # On ne permet pas la modification de l'email ou du username via cette vue de profil simple.
        # Ces actions nécessiteraient des flux de vérification plus complexes.
        # On ne garde que first_name et last_name pour la mise à jour.
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Créer un dictionnaire avec seulement les champs autorisés à la modification
        allowed_update_fields = ['first_name', 'last_name']
        data_for_update = {key: value for key, value in request.data.items() if key in allowed_update_fields}

        serializer = self.get_serializer(instance, data=data_for_update, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been used, then an object instances may have been cached separately
            # so make sure that we force reload it.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les Sociétés (Comptes Entreprise).
    Les utilisateurs ne peuvent gérer que les sociétés dont ils sont propriétaires.
    """
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOfCompany] # IsOwnerOfCompany pour PUT, PATCH, DELETE
                                                                      # Pour GET (liste) et POST, la logique est dans get_queryset et perform_create

    def get_queryset(self):
        """
        Cette vue doit retourner la liste des sociétés possédées par l'utilisateur connecté.
        """
        # request.user est l'utilisateur authentifié grâce à TokenAuthentication
        return Company.objects.filter(owner=self.request.user).order_by('name')

    def perform_create(self, serializer):
        """
        Assigne l'utilisateur connecté comme propriétaire de la nouvelle société.
        """
        serializer.save(owner=self.request.user)

    # Les permissions pour les actions de détail (retrieve, update, destroy)
    # sont gérées par IsOwnerOfCompany qui est appelé par `self.check_object_permissions(self.request, obj)`

    # Exemple d'action personnalisée si nécessaire:
    # from rest_framework.decorators import action
    # @action(detail=True, methods=['post'])
    # def set_active(self, request, pk=None):
    #     company = self.get_object() # Ceci va vérifier les permissions d'objet
    #     # Logique pour définir cette société comme active pour l'utilisateur en session
    #     # request.session['active_company_id'] = company.id
    #     # request.session['active_company_name'] = company.name
    #     return Response({'status': 'société active définie', 'company_id': company.id, 'company_name': company.name})


# Ajouter ici les vues pour PasswordChange, PasswordReset, etc. si nécessaire pour l'API.
# DRF fournit des vues pour cela dans `django.contrib.auth.views` qui rendent des templates HTML.
# Pour une API pure, il faudrait des vues API spécifiques ou utiliser des packages comme `dj_rest_auth`.
# Pour le MVP, on peut se concentrer sur l'essentiel et gérer le reset via l'admin Django ou un flux simple.
# Si on utilise dj_rest_auth, il fournit déjà ces endpoints.
# Pour l'instant, on les laisse en suspens pour se concentrer sur le CRUD de base.
# Si on les implémente manuellement :

# class PasswordChangeView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = PasswordChangeSerializer # A créer dans serializers.py

#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         request.user.set_password(serializer.validated_data['new_password'])
#         request.user.save()
#         return Response({"detail": "Mot de passe changé avec succès."}, status=status.HTTP_200_OK)

# etc. pour password reset.
