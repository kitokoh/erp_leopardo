# Conception du Projet Web - Client Document Manager

## 1. Introduction et Objectifs

Ce document détaille la conception de la version web de l'application Client Document Manager. L'application de bureau existante est très complète et offre une richesse fonctionnelle importante.

L' **objectif principal** de cette version web est de fournir une accessibilité accrue aux fonctionnalités clés de l'application depuis n'importe quel appareil disposant d'un navigateur web, sans nécessité d'installation logicielle. Elle vise à construire une plateforme web robuste et autonome, incluant sa propre API et gestion de base de données.

**Valeur ajoutée attendue :**

*   **Accessibilité Universelle** : Accès depuis n'importe quel OS (Windows, macOS, Linux, etc.) via un navigateur.
*   **Facilité de Déploiement et de Mise à Jour** : Mises à jour centralisées côté serveur, bénéficiant immédiatement à tous les utilisateurs.
*   **API Dédiée et Moderne** : Une API construite avec Django REST Framework pour servir le frontend web et potentiellement de futurs clients (ex: une nouvelle application mobile).
*   **Base de Données Robuste** : Utilisation de PostgreSQL pour une meilleure scalabilité et gestion des accès concurrents par rapport à SQLite.
*   **Aucune Installation Requise** : Simplifie l'accès pour les utilisateurs.
*   **Potentiel Collaboratif** : Ouvre la voie à des fonctionnalités collaboratives plus aisées.

L'application web sera développée comme une solution complète et indépendante, s'inspirant des fonctionnalités de l'application de bureau mais avec sa propre architecture backend et base de données.

## 2. Public Cible

Le public cible pour l'application web :

*   **Commerciaux / Équipes de Vente** : Consultation de fiches clients, historique des documents, génération de documents commerciaux.
*   **Managers / Décideurs** : Accès aux tableaux de bord, rapports clés, suivi des activités.
*   **Support Client / SAV** : Accès aux informations clients et historique.
*   **Employés en télétravail ou en déplacement** : Accès facilité aux outils.
*   **(Potentiel Futur)** Utilisateurs externes pour partage sécurisé de documents.

## 3. Architecture Technologique Proposée

L'application web sera construite sur une stack Python/Django, avec une API dédiée et une base de données PostgreSQL.

### 3.1. Backend

*   **Framework** : **Django (Python)**
*   **Justification** :
    *   **Écosystème Robuste** : Framework "batteries included" (ORM, admin, authentification, sécurité).
    *   **Cohérence Technologique** : Python est déjà utilisé dans le projet existant.
    *   **ORM Puissant** : Facilite les interactions avec PostgreSQL.
    *   **Sécurité Intégrée** : Protections contre les failles web courantes.
    *   **Interface d'Administration** : Atout majeur pour la gestion des données.
    *   **Scalabilité** : Capable de gérer des applications de taille importante.

### 3.2. API (Application Programming Interface)

*   **Framework** : **Django REST Framework (DRF)**, intégré au projet Django.
*   **Rôle** : Servir de backend pour le frontend de l'application web elle-même. Pourrait également être consommée par d'autres clients à l'avenir (ex: une nouvelle application mobile).
*   **Principes** :
    *   **RESTful** : Suivre les principes REST pour la conception des endpoints.
    *   **Authentification** : Basée sur les tokens (ex: `TokenAuthentication` de DRF ou JWT).
    *   **Permissions** : Gestion fine des accès aux ressources via le système de permissions de DRF.
    *   **Serializers** : Pour la conversion des objets Django (models) en JSON et vice-versa, et pour la validation des données.
    *   **ViewSets/APIViews** : Pour structurer la logique des endpoints.
    *   **Documentation d'API** : Utilisation d'outils comme `drf-spectacular` (pour OpenAPI/Swagger) pour générer automatiquement la documentation de l'API.
*   **Exemples d'Endpoints (non exhaustif)** :
    *   `/api/users/login/`, `/api/users/register/`, `/api/users/me/`
    *   `/api/clients/`, `/api/clients/<id>/`
    *   `/api/products/`, `/api/products/<id>/`
    *   `/api/documents/`, `/api/documents/<id>/`, `/api/documents/generate_proforma/`
    *   `/api/companies/`, `/api/companies/<id>/` (si gestion multi-sociétés)

### 3.3. Frontend

*   **Approche Proposée** : **Templates Django traditionnels enrichis avec HTMX et Alpine.js.**
*   **Justification** :
    *   **Développement Rapide (MVP)** : Permet de développer rapidement des interfaces dynamiques sans la complexité d'une SPA complète.
    *   **HTMX** : Pour des mises à jour partielles de la page et une interactivité riche en écrivant principalement du HTML côté serveur.
    *   **Alpine.js** : Pour les petites interactions côté client.
    *   **Simplicité et Évolution** : Moins de complexité d'outillage initial. Possibilité d'intégrer des composants Vue/React plus tard si nécessaire.
*   **Framework CSS suggéré** : **Bootstrap 5** (responsive, composants prêts à l'emploi).

### 3.4. Base de Données

*   **Système de Gestion de Base de Données (SGBD)** : **PostgreSQL**
*   **Justification** :
    *   **Robustesse et Fiabilité** : PostgreSQL est reconnu pour sa stabilité et son intégrité des données.
    *   **Fonctionnalités Avancées** : Supporte des types de données complexes, des indexations avancées, des transactions ACID.
    *   **Scalabilité** : Gère mieux la concurrence et les volumes de données importants que SQLite, ce qui est crucial pour une application web.
    *   **Bien Intégré avec Django** : Django a un excellent support pour PostgreSQL.
    *   **Standard de l'Industrie** : Largement utilisé pour les applications web professionnelles.
*   **ORM** : L'ORM de Django sera utilisé pour toutes les interactions avec la base de données.

### 3.5. Communication entre Composants

*   Le frontend (templates Django + HTMX/Alpine.js) communiquera avec le backend Django (vues Django) via des requêtes HTTP standards.
*   Les vues Django interagiront avec l'API DRF (si certaines logiques sont mieux gérées via l'API interne) ou directement avec les modèles Django et l'ORM pour les opérations CRUD.
*   Pour les opérations asynchrones ou les tâches longues (ex: génération de documents complexes), **Celery** avec un message broker comme **Redis** ou **RabbitMQ** sera envisagé.

## 4. Modèles de Données Django (avec PostgreSQL)

Voici une proposition initiale pour les modèles principaux. Les types de champs sont des exemples et pourront être affinés. `models.ForeignKey` avec `on_delete=models.SET_NULL` ou `models.PROTECT` sera utilisé judicieusement.

```python
# common/models.py (pour les modèles de base/abstraits)
from django.db import models
import uuid

class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from common.models import TimeStampedModel # Assumant que TimeStampedModel est dans common

class User(AbstractUser, TimeStampedModel): # Hérite de TimeStampedModel pour id UUID si souhaité, sinon AbstractUser a déjà un id auto-incrémenté
    # AbstractUser fournit déjà username, first_name, last_name, email, password, is_staff, is_active, date_joined etc.
    # Ajouter des champs spécifiques si nécessaire, par exemple :
    # profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    # phone_number = models.CharField(max_length=20, null=True, blank=True)

    # Si on n'utilise pas l'id UUID de TimeStampedModel pour User:
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # Décommenter si on veut forcer UUID pour User

    def __str__(self):
        return self.username

class Company(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    # ... autres champs (SIRET, TVA, etc.)
    owner = models.ForeignKey(User, related_name='owned_companies', on_delete=models.CASCADE) # Qui a créé/possède cette société
    # Si un utilisateur peut appartenir à plusieurs sociétés avec des rôles différents:
    # members = models.ManyToManyField(User, through='Membership', related_name='companies')

    def __str__(self):
        return self.name

# class Membership(TimeStampedModel):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     company = models.ForeignKey(Company, on_delete=models.CASCADE)
#     role = models.CharField(max_length=100) # ex: 'admin', 'member'
#     # ... autres champs liés à l'appartenance

# clients/models.py
class Client(TimeStampedModel):
    company_account = models.ForeignKey(Company, related_name='clients', on_delete=models.CASCADE) # La société à laquelle ce client appartient
    client_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    # ... autres champs (contact principal, notes, etc.)

    def __str__(self):
        return self.client_name

# products/models.py
class ProductCategory(TimeStampedModel):
    company_account = models.ForeignKey(Company, related_name='product_categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(TimeStampedModel):
    company_account = models.ForeignKey(Company, related_name='products', on_delete=models.CASCADE)
    category = models.ForeignKey(ProductCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, null=True, blank=True, unique=True) # Peut-être unique par Company
    description = models.TextField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    # image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    # stock = models.IntegerField(default=0)
    # ... autres champs (dimensions, poids, fournisseur)

    def __str__(self):
        return self.name

# documents/models.py
class Document(TimeStampedModel):
    DOCUMENT_TYPE_CHOICES = [
        ('PROFORMA', 'Facture Proforma'),
        ('INVOICE', 'Facture'),
        ('QUOTE', 'Devis'),
        ('CONTRACT', 'Contrat'),
        # ... autres types
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SENT', 'Envoyé'),
        ('PAID', 'Payé'),
        ('CANCELLED', 'Annulé'),
    ]

    company_account = models.ForeignKey(Company, related_name='documents', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name='documents', on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_reference = models.CharField(max_length=100, unique=True) # Logique de génération à définir
    issue_date = models.DateField(default=timezone.now) # from django.utils import timezone
    due_date = models.DateField(null=True, blank=True)
    total_amount_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00) # Exemple de taux de TVA
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='created_documents', on_delete=models.SET_NULL, null=True)
    # file_pdf = models.FileField(upload_to='documents_pdf/', null=True, blank=True) # Si on stocke le PDF généré

    def __str__(self):
        return f"{self.get_document_type_display()} {self.document_reference} - {self.client.client_name}"

class DocumentItem(TimeStampedModel):
    document = models.ForeignKey(Document, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='document_items', on_delete=models.SET_NULL, null=True) # Ou PROTECT
    description = models.CharField(max_length=255) # Peut être pré-rempli par le produit, mais modifiable
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    unit_price_ht = models.DecimalField(max_digits=10, decimal_places=2) # HT
    total_item_ht = models.DecimalField(max_digits=12, decimal_places=2) # HT

    def save(self, *args, **kwargs):
        self.total_item_ht = self.quantity * self.unit_price_ht
        super().save(*args, **kwargs)
        # Mettre à jour les totaux du document parent
        self.document.update_totals()


    def __str__(self):
        return f"{self.quantity} x {self.description}"

# Dans Document model:
# def update_totals(self):
#     items = self.items.all()
#     self.total_amount_ht = sum(item.total_item_ht for item in items)
#     # Calculer TTC en fonction de self.tax_rate
#     self.total_amount_ttc = self.total_amount_ht * (1 + (self.tax_rate / 100))
#     self.save(update_fields=['total_amount_ht', 'total_amount_ttc'])

```
**Note Importante sur `TimeStampedModel` et `User`**:
Le modèle `User` de Django hérite de `AbstractUser` qui a déjà un champ `id` auto-incrémenté (Integer). Si vous souhaitez utiliser un `UUID` comme clé primaire pour `User` également (pour la cohérence avec les autres modèles utilisant `TimeStampedModel`), vous devrez créer un modèle `User` personnalisé qui hérite de `AbstractBaseUser` et `PermissionsMixin` et définir explicitement le champ `id` comme `UUIDField`. Pour simplifier le MVP, on peut conserver l'ID entier pour `User` et utiliser `TimeStampedModel` pour les autres modèles. L'exemple ci-dessus montre comment `User` pourrait hériter de `TimeStampedModel` mais cela nécessite une attention particulière si on garde `AbstractUser`. Une approche plus simple est de ne pas faire hériter `User` de `TimeStampedModel` et d'ajouter `created_at`/`updated_at` manuellement si besoin pour le modèle `User`. L'exemple a été ajusté pour clarifier cela.

## 5. API avec Django REST Framework (DRF)

L'API sera le cœur de la communication de données pour l'application.

### 5.1. Serializers (`serializers.py` dans chaque app)

Les serializers définissent comment les données des modèles sont converties en JSON et vice-versa, et gèrent la validation.

```python
# products/serializers.py
from rest_framework import serializers
from .models import Product, ProductCategory

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'company_account'] # company_account pour filtrage/validation

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True) # Pour afficher le nom

    class Meta:
        model = Product
        fields = ['id', 'name', 'reference', 'description', 'unit_price', 'category', 'category_name', 'company_account']
        read_only_fields = ['id', 'category_name']

# users/serializers.py
from rest_framework import serializers
from .models import User, Company
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        # Possibilité d'ajouter d'autres validations (ex: complexité du mot de passe)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff'] # Ajouter d'autres champs si besoin

class CompanySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'name', 'address', 'logo', 'owner', 'owner_username']
        extra_kwargs = {
            'owner': {'read_only': True} # L'owner est défini par l'utilisateur connecté lors de la création
        }


# documents/serializers.py
from rest_framework import serializers
from .models import Document, DocumentItem
from clients.serializers import ClientSerializer # Importer pour imbrication si besoin
from products.serializers import ProductSerializer # Importer pour imbrication si besoin

class DocumentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentItem
        fields = ['id', 'product', 'description', 'quantity', 'unit_price_ht', 'total_item_ht']
        read_only_fields = ['total_item_ht']

class DocumentSerializer(serializers.ModelSerializer):
    items = DocumentItemSerializer(many=True) # Pour créer/mettre à jour les items avec le document
    client_details = ClientSerializer(source='client', read_only=True) # Pour afficher les détails du client en lecture
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'document_reference', 'issue_date', 'due_date',
            'total_amount_ht', 'total_amount_ttc', 'tax_rate', 'status', 'notes',
            'client', 'client_details', 'items', 'company_account',
            'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'document_reference', 'total_amount_ht', 'total_amount_ttc', 'created_by_username', 'client_details']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        document = Document.objects.create(**validated_data)
        for item_data in items_data:
            DocumentItem.objects.create(document=document, **item_data)
        document.update_totals() # Recalculer les totaux après création des items
        return document

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None) # items est optionnel en update

        # Mettre à jour les champs simples de Document
        instance.client = validated_data.get('client', instance.client)
        instance.document_type = validated_data.get('document_type', instance.document_type)
        # ... autres champs ...
        instance.status = validated_data.get('status', instance.status)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()

        if items_data is not None:
            # Logique pour mettre à jour les items (plus complexe: suppression, ajout, modification)
            # Pour simplifier le MVP, on peut exiger que tous les items soient renvoyés
            # et on supprime les anciens pour recréer les nouveaux.
            instance.items.all().delete()
            for item_data in items_data:
                DocumentItem.objects.create(document=instance, **item_data)

        instance.update_totals()
        return instance
```

### 5.2. Vues (`ViewSets` ou `APIView` dans `views.py` de chaque app)

Les vues gèrent la logique de réception des requêtes HTTP et de renvoi des réponses.

```python
# products/views.py
from rest_framework import viewsets, permissions
from .models import Product, ProductCategory
from .serializers import ProductSerializer, ProductCategorySerializer

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser uniquement les propriétaires d'un objet à le modifier.
    Lecture autorisée pour tous.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS: # GET, HEAD, OPTIONS
            return True
        # Nécessite que les modèles aient un champ 'company_account' et que company_account ait un 'owner'
        # Ou que les modèles aient un champ 'created_by' ou 'owner' direct.
        # Adapter cette logique à la structure exacte de propriété.
        # Pour l'exemple, on assume que company_account.owner est l'utilisateur propriétaire.
        if hasattr(obj, 'company_account') and obj.company_account.owner == request.user:
            return True
        if hasattr(obj, 'owner') and obj.owner == request.user:
             return True
        return False


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly] # Exemple

    def get_queryset(self):
        # Filtrer les produits par la société de l'utilisateur connecté
        # Assumant que l'utilisateur a une ou plusieurs sociétés associées
        # ou qu'on sélectionne une "société active"
        user = self.request.user
        # Exemple: si l'utilisateur a une company active stockée dans son profil ou session
        # active_company = get_active_company_for_user(user)
        # return Product.objects.filter(company_account=active_company)
        # Pour l'instant, retournons tous les produits si superuser, sinon ceux liés à ses sociétés
        if user.is_superuser:
            return Product.objects.all()

        # Trouver les sociétés dont l'utilisateur est propriétaire
        user_owned_companies = Company.objects.filter(owner=user)
        return Product.objects.filter(company_account__in=user_owned_companies)


    def perform_create(self, serializer):
        # Assigner la société active de l'utilisateur lors de la création
        # active_company = get_active_company_for_user(self.request.user)
        # serializer.save(company_account=active_company)
        # Pour l'exemple, on prend la première société possédée par l'utilisateur
        active_company = Company.objects.filter(owner=self.request.user).first()
        if not active_company:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous devez posséder une société pour créer un produit.")
        serializer.save(company_account=active_company)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ProductCategory.objects.all()
        user_owned_companies = Company.objects.filter(owner=user)
        return ProductCategory.objects.filter(company_account__in=user_owned_companies)

    def perform_create(self, serializer):
        active_company = Company.objects.filter(owner=self.request.user).first()
        if not active_company:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous devez posséder une société pour créer une catégorie.")
        serializer.save(company_account=active_company)

# users/views.py
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from .serializers import UserRegistrationSerializer, UserSerializer, CompanySerializer
from .models import Company

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny] # Tout le monde peut s'inscrire

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Créer un token pour le nouvel utilisateur
        token, created = Token.objects.get_or_create(user=user)
        # Créer une société par défaut pour ce nouvel utilisateur
        # Pour simplifier, le nom de la société sera "Société de [username]"
        default_company_name = f"Société de {user.username}"
        Company.objects.create(name=default_company_name, owner=user)

        return Response(
            {"user": UserSerializer(user, context=self.get_serializer_context()).data, "token": token.key},
            status=status.HTTP_201_CREATED
        )

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.pk, 'email': user.email, 'username': user.username})

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user # L'utilisateur ne peut voir/modifier que son propre profil

class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # L'utilisateur ne voit que les sociétés qu'il possède
        return Company.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # L'utilisateur connecté devient propriétaire de la société créée
        serializer.save(owner=self.request.user)


# documents/views.py
from rest_framework import viewsets, permissions
from .models import Document # DocumentItem sera géré via le DocumentSerializer
from .serializers import DocumentSerializer
# from .permissions import IsDocumentOwner # Permission personnalisée si besoin

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly] # IsOwnerOrReadOnly doit être adapté pour Document

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Document.objects.all()
        # Filtrer les documents par la/les société(s) de l'utilisateur
        user_owned_companies = Company.objects.filter(owner=user)
        return Document.objects.filter(company_account__in=user_owned_companies).select_related('client', 'created_by').prefetch_related('items__product')


    def perform_create(self, serializer):
        user = self.request.user
        # Assigner la société basée sur le client ou une sélection explicite
        # Pour l'instant, on assume que company_account est fourni dans les données
        # ou on prend la première société de l'utilisateur
        company_id_from_request = self.request.data.get('company_account')
        active_company = None
        if company_id_from_request:
            active_company = Company.objects.filter(id=company_id_from_request, owner=user).first()
            if not active_company:
                 from rest_framework.exceptions import PermissionDenied
                 raise PermissionDenied("La société spécifiée n'est pas valide ou ne vous appartient pas.")
        else: # Prendre la première société de l'utilisateur par défaut
            active_company = Company.objects.filter(owner=user).first()
            if not active_company:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous devez posséder une société pour créer un document.")

        # Générer une référence unique pour le document (logique à affiner)
        # Exemple simple : TYPE-COMPANYID-TIMESTAMP
        doc_type_prefix = serializer.validated_data.get('document_type', 'DOC')[:3]
        import time
        timestamp_suffix = int(time.time())
        generated_reference = f"{doc_type_prefix.upper()}-{active_company.id.hex[:4].upper()}-{timestamp_suffix}"

        serializer.save(created_by=user, company_account=active_company, document_reference=generated_reference)

```

### 5.3. URLs de l'API (`urls.py` dans chaque app et dans `clientdoc_web/urls.py`)

```python
# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductCategoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', ProductCategoryViewSet, basename='productcategory')

urlpatterns = [
    path('', include(router.urls)),
]

# users/urls.py
from django.urls import path, include
from .views import UserRegistrationView, CustomAuthToken, UserDetailView, CompanyViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', CustomAuthToken.as_view(), name='user-login'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('', include(router.urls)), # Pour /api/users/companies/
]

# documents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]


# clientdoc_web/urls.py (fichier principal d'URLs du projet)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Pour les fichiers médias en dev
from django.conf.urls.static import static # Pour les fichiers médias en dev

urlpatterns = [
    path('admin/', admin.site.urls),
    # API URLs
    path('api/users/', include('apps.users.urls')), # apps.users.urls ou users.urls selon structure
    path('api/products/', include('apps.products.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/clients/', include('apps.clients.urls')), # À créer
    # URLs pour le frontend Django (templates)
    # path('', include('apps.dashboard.urls')), # Page d'accueil/dashboard
    # ... autres URLs pour les vues rendant des templates HTML
]

# Servir les fichiers médias en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

```

### 5.4. Authentification et Permissions

*   **Authentification** : `rest_framework.authtoken.models.Token` pour l'authentification basée sur les tokens. Un token est généré pour l'utilisateur lors de la connexion/inscription et doit être inclus dans l'en-tête `Authorization` des requêtes API (ex: `Authorization: Token <token_value>`).
*   **Permissions** :
    *   `permissions.IsAuthenticated` : Accès réservé aux utilisateurs connectés.
    *   `permissions.AllowAny` : Pour les endpoints publics (ex: inscription, connexion).
    *   Permissions personnalisées (comme `IsOwnerOrReadOnly` esquissée plus haut) pour contrôler l'accès aux objets spécifiques en fonction de leur propriétaire ou de la société associée. Elles seront cruciales pour le multi-tenant (si chaque utilisateur/société ne voit que ses propres données).

### 5.5. Documentation d'API

*   Installer `drf-spectacular`: `pip install drf-spectacular`
*   Ajouter `'drf_spectacular',` à `INSTALLED_APPS`.
*   Ajouter les URLs pour Swagger UI et ReDoc dans `clientdoc_web/urls.py`:
    ```python
    # clientdoc_web/urls.py
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
    # ...
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
    ```

## 6. Structure Détaillée des "Apps" Django

Chaque "app" Django (ex: `users`, `products`, `documents`, `clients`, `dashboard`) suivra une structure standardisée :

```
apps/
├── users/
│   ├── __init__.py
│   ├── admin.py         # Configuration pour l'interface d'admin Django
│   ├── apps.py          # Configuration de l'application
│   ├── models.py        # Définition des modèles de données (User, Company)
│   ├── serializers.py   # Serializers DRF pour User, Company
│   ├── views.py         # Vues API (UserRegistration, Login, UserDetail, CompanyViewSet) et vues pour templates si besoin
│   ├── urls.py          # URLs spécifiques à l'app users (API et templates)
│   ├── forms.py         # Formulaires Django (ex: pour l'inscription, profil si rendu via templates Django)
│   ├── templates/       # Templates HTML spécifiques à l'app users
│   │   └── users/
│   │       ├── login.html
│   │       └── register.html
│   ├── migrations/      # Générées par Django pour les changements de modèles
│   └── tests/           # Tests pour cette application (non détaillé ici)
│       └── __init__.py
├── products/
│   ├── ... (structure similaire: models.py, serializers.py, views.py (API+templates), urls.py, forms.py, templates/products/)
├── documents/
│   ├── ...
├── clients/
│   ├── ...
└── dashboard/           # Pour la page d'accueil après connexion
    ├── views.py         # Vue pour rendre le template du dashboard
    ├── urls.py
    └── templates/
        └── dashboard/
            └── main_dashboard.html
```

**Contenu type des fichiers :**

*   **`models.py`**: Contient les définitions des classes de modèles Django (tables de la base de données). (Détaillé en section 4)
*   **`serializers.py`**: Contient les classes de serializers DRF pour convertir les modèles en JSON et valider les données entrantes. (Détaillé en section 5.1)
*   **`views.py`**:
    *   Pour l'API : `APIView` ou `ViewSet` de DRF pour exposer les endpoints. (Détaillé en section 5.2)
    *   Pour le Frontend : Vues Django classiques (`View`, `TemplateView`, `FormView`, etc.) qui rendent les templates HTML, traitent les formulaires, et interagissent avec les modèles ou appellent des services/API.
*   **`urls.py`**: Mappage des URLs aux vues (API et frontend). (Détaillé en section 5.3)
*   **`forms.py`**: Définition des `django.forms.Form` ou `django.forms.ModelForm` pour la validation et le rendu des formulaires dans les templates Django.
    ```python
    # users/forms.py (exemple pour le frontend Django, pas pour l'API DRF directement)
    from django import forms
    from .models import User # ou get_user_model()

    class UserRegistrationForm(forms.ModelForm): # Si on utilise les formulaires Django pour le rendu HTML
        password = forms.CharField(widget=forms.PasswordInput)
        password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

        class Meta:
            model = User # Assurez-vous que User est bien le modèle utilisateur de votre projet
            fields = ['username', 'email', 'first_name', 'last_name']

        def clean_password2(self):
            cd = self.cleaned_data
            if cd['password'] != cd['password2']:
                raise forms.ValidationError('Passwords don\'t match.')
            return cd['password2']
    ```
*   **`admin.py`**: Enregistrement des modèles pour qu'ils apparaissent dans l'interface d'administration de Django.
    ```python
    # products/admin.py
    from django.contrib import admin
    from .models import Product, ProductCategory

    @admin.register(Product)
    class ProductAdmin(admin.ModelAdmin):
        list_display = ('name', 'reference', 'category', 'unit_price', 'company_account', 'created_at')
        list_filter = ('category', 'company_account', 'created_at')
        search_fields = ('name', 'reference', 'description')

    @admin.register(ProductCategory)
    class ProductCategoryAdmin(admin.ModelAdmin):
        list_display = ('name', 'company_account', 'created_at')
        search_fields = ('name',)
    ```
*   **`templates/app_name/`**: Fichiers HTML pour les vues de cette application.

## 7. Détail des Fonctionnalités (MVP)

### 7.1. Authentification Utilisateur

*   **Inscription (`/api/users/register/` et page HTML `/auth/register/`)**
    *   **Backend (API)**: `UserRegistrationView` (cf. section 5.2). Crée l'utilisateur, un token, et une `Company` par défaut.
    *   **Backend (Vue Django pour HTML)**:
        *   `views.py`: Une vue qui affiche `UserRegistrationForm`. En cas de succès, appelle l'API d'inscription ou utilise directement la logique de création d'utilisateur.
        *   Si succès, connecte l'utilisateur et le redirige vers le dashboard.
    *   **Template HTML (`users/register.html`)**: Formulaire avec champs username, email, prénom, nom, password, password2. Affichage des erreurs.
    *   **Frontend (HTMX/Alpine)**: Validation de base côté client (champs requis). Soumission via POST. HTMX peut être utilisé pour afficher les erreurs de validation sans recharger toute la page.
*   **Connexion (`/api/users/login/` et page HTML `/auth/login/`)**
    *   **Backend (API)**: `CustomAuthToken` (cf. section 5.2). Retourne token et infos utilisateur.
    *   **Backend (Vue Django pour HTML)**:
        *   `views.py`: Affiche un formulaire de connexion. En cas de succès, stocke le token dans la session de l'utilisateur (ou cookie sécurisé) et redirige.
    *   **Template HTML (`users/login.html`)**: Formulaire username, password.
    *   **Frontend**: Soumission via POST.
*   **Déconnexion (Page HTML `/auth/logout/`)**
    *   **Backend (Vue Django)**: Efface le token de la session/cookie. Invalide le token côté serveur si possible (nécessite une table de tokens blacklistés ou un autre mécanisme). Redirige vers la page de connexion.
    *   L'API DRF n'a généralement pas de endpoint "logout" pour TokenAuthentication simple, la suppression du token côté client suffit. Pour une sécurité accrue, on pourrait implémenter un endpoint qui ajoute le token à une liste noire jusqu'à son expiration.

### 7.2. Tableau de Bord Principal (`/dashboard/`)

*   **Backend (Vue Django `dashboard/views.py`)**:
    *   Récupère les informations à afficher (ex: 5 derniers documents, nombre de clients, via des appels à l'API interne ou des requêtes ORM directes si performant et sécurisé).
    *   Passe les données au template.
*   **Template HTML (`dashboard/main_dashboard.html`)**:
    *   Structure de la page principale avec menu de navigation.
    *   Sections pour afficher les résumés (ex: cartes Bootstrap).
    *   Liens vers les modules principaux.
*   **Frontend**: Affichage statique des données fournies par le backend.

### 7.3. Module Clients

*   **Liste des Clients (`/clients/`)**
    *   **Backend (Vue Django)**: Récupère la liste des clients (paginée) via l'API (`/api/clients/`) ou ORM. Passe au template.
    *   **Template HTML (`clients/client_list.html`)**: Tableau affichant les clients (nom, email, téléphone). Liens vers la vue détaillée. Outils de pagination. Formulaire de recherche/filtre.
    *   **Frontend (HTMX)**: La recherche/filtre et la pagination peuvent recharger uniquement la section du tableau via HTMX.
*   **Vue Détaillée d'un Client (`/clients/<id>/`)**
    *   **Backend (Vue Django)**: Récupère les détails du client et ses documents associés via l'API ou ORM.
    *   **Template HTML (`clients/client_detail.html`)**: Affiche toutes les infos du client. Liste des documents liés.
*   **(Optionnel MVP) Création/Édition Client (`/clients/add/`, `/clients/<id>/edit/`)**
    *   **Backend (Vue Django)**: Vues avec `ModelForm` pour Client. En cas de succès, appelle l'API de création/modification (`POST` ou `PUT` sur `/api/clients/`).
    *   **Templates HTML**: Formulaires pour la saisie des informations.

### 7.4. Module Produits (Similaire à Clients)

*   Liste des Produits (`/products/`)
*   Vue Détaillée (`/products/<id>/`)

### 7.5. Module Documents

*   **Liste des Documents (`/documents/`)**
    *   **Backend (Vue Django)**: Récupère la liste (paginée, filtrable par type/statut/client) via l'API (`/api/documents/`) ou ORM.
    *   **Template HTML (`documents/document_list.html`)**: Tableau des documents. Filtres. Lien vers génération.
    *   **Frontend (HTMX)**: Filtres et pagination avec HTMX.
*   **Vue Détaillée d'un Document (`/documents/<id>/`)**
    *   **Backend (Vue Django)**: Récupère les détails du document et ses items.
    *   **Template HTML (`documents/document_detail.html`)**: Affiche les infos du document, la liste des items. Bouton pour télécharger PDF (si l'API le fournit).
*   **Génération de Facture Proforma (`/documents/proforma/add/`)**
    *   **Backend (Vue Django)**:
        *   GET: Affiche un formulaire multi-étapes ou une page unique.
            *   Sélection du client (peut-être avec auto-complétion via un appel HTMX à une API de recherche client).
            *   Formset pour les `DocumentItem`. Chaque ligne permet de sélectionner un produit (auto-complétion) ou de saisir une description libre, quantité, prix unitaire.
            *   Champs pour date d'émission, notes, taux de TVA.
        *   POST: Valide les données. Construit le payload JSON pour l'API `/api/documents/` (avec `document_type='PROFORMA'`). Appelle l'API.
        *   Si succès, redirige vers la vue détaillée du document créé ou affiche un message de succès avec lien.
    *   **Template HTML (`documents/proforma_form.html`)**:
        *   Formulaire pour les informations générales de la proforma.
        *   Gestion dynamique des lignes d'items (JavaScript/Alpine.js pour ajouter/supprimer des lignes, HTMX pour chercher des produits et pré-remplir).
        *   Calcul des totaux en temps réel (JavaScript/Alpine.js).
    *   **Frontend (HTMX/Alpine.js)**:
        *   Recherche de clients/produits en tapant (HTMX `hx-get` vers des endpoints API spécifiques).
        *   Ajout/suppression dynamique de lignes d'items.
        *   Calculs automatiques des totaux par ligne et totaux généraux.

## 8. Interface Utilisateur (UI) et Expérience Utilisateur (UX)

*   **Layout de Base (`templates/base.html`)**:
    *   Structure HTML commune (doctype, head, body).
    *   Inclusion de Bootstrap CSS & JS, HTMX, Alpine.js.
    *   Barre de navigation supérieure (logo, liens principaux, menu utilisateur avec profil/déconnexion).
    *   Sidebar (optionnel, pour navigation secondaire).
    *   Zone de contenu principal (`{% block content %}{% endblock %}`).
    *   Footer.
*   **Principes de Conception des Pages**:
    *   **Clarté des Formulaires**: Labels clairs, aides contextuelles, validation visible.
    *   **Tableaux de Données**: Lisibles, triables, avec pagination et filtres lorsque nécessaire.
    *   **Feedback Utilisateur**: Messages de succès, d'erreur, indicateurs de chargement (HTMX peut aider avec `hx-indicator`).
    *   **Responsive Design**: Test sur différentes tailles d'écran.

## 9. Composants Réutilisables (Exemples)

*   **Widget de Sélection de Client/Produit**: Un champ de texte avec auto-complétion qui charge les options depuis l'API via HTMX.
*   **Tableau de Données Paginé et Filtrable**: Un template Django incluable qui prend une liste d'objets et des options de configuration pour afficher un tableau avec des contrôles. HTMX sera utilisé pour mettre à jour le contenu du tableau sans recharger la page.
*   **Modales Bootstrap**: Pour des actions de confirmation, des formulaires rapides, affichage de détails sans quitter la page principale. Peuvent être déclenchées et remplies via HTMX.

## 10. Sécurité (Révision et Détails)

*   **Django Settings (`settings.py`)**:
    *   `SECRET_KEY` : Doit être unique et gardée secrète en production (gérée via variable d'environnement).
    *   `DEBUG = False` en production.
    *   `ALLOWED_HOSTS` : Configuré correctement en production.
    *   `CSRF_COOKIE_SECURE = True`, `SESSION_COOKIE_SECURE = True` (si HTTPS).
    *   Utilisation des middlewares de sécurité de Django (`SecurityMiddleware`).
*   **Django REST Framework**:
    *   `DEFAULT_AUTHENTICATION_CLASSES` et `DEFAULT_PERMISSION_CLASSES` configurés globalement ou par vue.
    *   Throttling (limitation du nombre de requêtes) pour protéger contre les abus.
*   **HTTPS**: Essentiel en production pour toutes les communications. Géré par le reverse proxy (Nginx).
*   **Gestion des Mots de Passe**: Utilisation des mécanismes de hachage de Django. Politiques de mot de passe robustes.
*   **Protection des Fichiers Uploadés**: Validation du type et de la taille des fichiers. Servir les fichiers médias de manière sécurisée.
*   **Mises à Jour Régulières**: Maintenir Django, DRF, Python, PostgreSQL et toutes les dépendances à jour.

## 11. Déploiement Gratuit en Phase de Développement

Pour permettre des tests et des démonstrations en continu durant le développement, une plateforme avec un niveau gratuit peut être utilisée. **Render.com** est une bonne option moderne.

**Étapes de base pour déployer une application Django avec PostgreSQL sur Render:**

1.  **Prérequis**:
    *   Application Django conteneurisable (avec un `Dockerfile` et un `render.yaml`).
    *   Code sur un dépôt Git (GitHub, GitLab).
2.  **Dockerfile**:
    ```dockerfile
    # Dockerfile
    FROM python:3.9-slim-buster

    ENV PYTHONDONTWRITEBYTECODE 1
    ENV PYTHONUNBUFFERED 1

    WORKDIR /app

    COPY requirements.txt /app/
    RUN pip install --no-cache-dir -r requirements.txt

    COPY . /app/

    # Commande pour collecter les statiques, si nécessaire au build
    # RUN python manage.py collectstatic --noinput
    # La collecte des statiques est souvent gérée par Whitenoise ou Nginx en prod

    # La commande de démarrage sera dans render.yaml
    ```
3.  **`requirements.txt`**: Doit inclure `Django`, `psycopg2-binary`, `gunicorn`, `djangorestframework`, `dj-database-url`, `whitenoise` (pour servir les statiques).
4.  **`render.yaml` (à la racine du projet)**:
    ```yaml
    services:
      - type: web # Service web pour Django
        name: clientdoc-web
        env: python
        region: frankfurt # Choisir une région
        plan: free # Niveau gratuit pour le service web
        buildCommand: "./build.sh" # Script pour les commandes de build
        startCommand: "gunicorn clientdoc_web.wsgi:application" # clientdoc_web est le nom de votre projet Django
        healthCheckPath: / # Un endpoint qui retourne 200 OK
        envVars:
          - key: DATABASE_URL
            fromDatabase:
              name: clientdoc-db # Nom du service de base de données défini ci-dessous
              property: connectionString
          - key: SECRET_KEY
            generateValue: true # Render génère une clé secrète
          - key: WEB_CONCURRENCY # Pour Gunicorn
            value: 4
          - key: PYTHON_VERSION
            value: 3.9.16 # Spécifier la version Python
        # autoDeploy: false # Mettre à true pour déploiement auto depuis Git

      - type: pserv # Service de base de données PostgreSQL
        name: clientdoc-db
        env: postgres
        region: frankfurt
        plan: free # Niveau gratuit pour PostgreSQL
        postgresMajorVersion: 14
        disk:
          sizeGB: 1 # Pour le niveau gratuit, souvent limité
    ```
5.  **`build.sh` (à la racine, exécutable)**:
    ```bash
    #!/usr/bin/env bash
    # exit on error
    set -o errexit

    pip install -r requirements.txt

    python manage.py collectstatic --no-input
    python manage.py migrate
    ```
6.  **Configuration Django (`settings.py`) pour Render**:
    ```python
    import dj_database_url
    import os

    # ...
    SECRET_KEY = os.environ.get('SECRET_KEY') # Lire depuis les variables d'env
    DEBUG = os.environ.get('DEBUG', 'False') == 'True' # Par défaut False en prod

    ALLOWED_HOSTS = ['.onrender.com'] # Ajouter l'URL de votre service Render
    # Si vous avez un domaine personnalisé, ajoutez-le aussi.

    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True if not DEBUG else False)
        # ssl_require=True est souvent nécessaire pour les DB Render en prod.
        # En dev local, vous utiliserez une config DB locale.
    }

    # Pour servir les fichiers statiques avec Whitenoise
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware') # Après SecurityMiddleware
    ```
7.  **Créer un "Blueprint" sur Render**: Connecter le dépôt Git, Render lira le `render.yaml` et provisionnera les services.

D'autres plateformes comme Heroku (avec Heroku CLI) ou PythonAnywhere (via leur interface web) ont des processus de déploiement différents mais le principe reste de configurer la base de données, les variables d'environnement et la commande de démarrage.

## 12. Flux de Données et Interactions Utilisateur (Illustrations à venir)

Cette section sera complétée par des descriptions textuelles ou des diagrammes simples (Mermaid.js si possible dans le Markdown) pour illustrer :

*   **Flux d'Inscription/Connexion**.
*   **Flux CRUD pour un Client** (Création, Liste, Détail, Mise à jour).
*   **Flux de Génération d'une Facture Proforma**.

*(Cette section sera développée ultérieurement dans le document)*

Ce document de conception approfondi servira de guide détaillé pour la phase de développement. Il sera mis à jour au besoin.
