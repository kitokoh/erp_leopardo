# Module : Spécifications de l'API (Django REST Framework)

## 1. Introduction et Objectifs

Ce document centralise les spécifications détaillées de l'API RESTful construite avec Django REST Framework (DRF). L'API sert de backend principal pour l'application web frontend (templates Django + HTMX/Alpine.js) et pourrait être utilisée par d'autres clients à l'avenir.

**Objectifs Clés :**

*   Fournir une interface de programmation claire, cohérente et sécurisée pour toutes les opérations sur les données.
*   Définir les ressources, les endpoints, les formats de données (JSON), les méthodes HTTP.
*   Spécifier l'authentification, les permissions, la validation des données, la pagination et le filtrage.
*   Faciliter la génération automatique de la documentation de l'API.

## 2. Principes Généraux de l'API

*   **Format des Données** : JSON exclusivement.
*   **Méthodes HTTP Standards** :
    *   `GET` : Récupérer des ressources.
    *   `POST` : Créer de nouvelles ressources.
    *   `PUT` : Mettre à jour intégralement une ressource existante.
    *   `PATCH` : Mettre à jour partiellement une ressource existante.
    *   `DELETE` : Supprimer une ressource.
*   **URLs (Endpoints)** : Structure d'URL basée sur les ressources, ex: `/api/clients/`, `/api/products/<id>/`.
*   **Gestion des Erreurs** : Utilisation des codes de statut HTTP standards (200, 201, 204, 400, 401, 403, 404, 500). Les réponses d'erreur (4xx, 5xx) incluront un corps JSON avec des détails sur l'erreur (ex: `{"detail": "Message d'erreur", "field_errors": {"nom_champ": ["erreur1"]}}`).
*   **Versionnement (Optionnel pour MVP)** : Si nécessaire à l'avenir, via l'URL (`/api/v1/...`) ou les en-têtes `Accept`. Pour le MVP, pas de versionnement explicite.
*   **Filtrage, Tri, Pagination** :
    *   **Filtrage** : Via paramètres d'URL (ex: `/api/documents/?status=SENT&client_id=...`). `django-filter` sera utilisé.
    *   **Tri** : Via paramètre d'URL (ex: `/api/products/?ordering=name` ou `?ordering=-unit_price`).
    *   **Pagination** : Pagination basée sur les pages (`PageNumberPagination` de DRF), avec des liens `next` et `previous` dans la réponse.

## 3. Authentification et Permissions

*   **Authentification par Token** :
    *   Utilisation de `rest_framework.authtoken.models.Token`.
    *   Un token est généré lors de l'inscription (`POST /api/users/register/`) ou de la connexion (`POST /api/users/login/`).
    *   Le token doit être inclus dans l'en-tête `Authorization` des requêtes nécessitant une authentification : `Authorization: Token <your_token_here>`.
*   **Permissions (`permission_classes` dans les vues DRF)** :
    *   `permissions.IsAuthenticated` : Seuls les utilisateurs connectés peuvent accéder à l'endpoint.
    *   `permissions.AllowAny` : Accès public (ex: pour inscription, connexion).
    *   `permissions.IsAdminUser` : Seuls les utilisateurs avec `is_staff=True` peuvent accéder.
    *   **Permissions Personnalisées** : Des classes de permission personnalisées seront créées pour gérer la logique métier spécifique, notamment pour s'assurer qu'un utilisateur ne peut accéder/modifier que les données appartenant à sa société (ou aux sociétés dont il est membre/propriétaire).
        *   Exemple : `IsOwnerOfCompanyData(permissions.BasePermission)` qui vérifierait que l'objet demandé (Client, Produit, Document) a un champ `company_account` qui correspond à une société gérée par `request.user`.

## 4. Documentation de l'API

*   Utilisation de **`drf-spectacular`** pour générer un schéma OpenAPI 3.
*   Endpoints pour la documentation :
    *   `/api/schema/` (Schéma OpenAPI JSON/YAML)
    *   `/api/schema/swagger-ui/` (Interface utilisateur Swagger)
    *   `/api/schema/redoc/` (Interface utilisateur ReDoc)
*   Les docstrings des vues DRF et des serializers seront utilisées pour enrichir la documentation générée.

## 5. Structure des Endpoints et Spécifications Détaillées

Les modèles Django (`User`, `Company`, `Client`, `ProductCategory`, `Product`, `Document`, `DocumentItem`) sont décrits dans `00_architecture_globale.md` et dans les documents de conception de chaque module.

### 5.1. Module Utilisateurs et Sociétés (`/api/users/`)

Voir `00_architecture_globale.md` (section 5.2 et 5.3 pour exemples de serializers/vues) et `01_utilisateurs_authentification.md` / `02_societes_gestion.md`.

#### 5.1.1. `User` Endpoints

*   **`POST /api/users/register/`**
    *   **Description** : Inscription d'un nouvel utilisateur. Crée aussi une `Company` par défaut pour cet utilisateur.
    *   **Permissions** : `AllowAny`.
    *   **Request Body** (`UserRegistrationSerializer`) : `username`, `email`, `password`, `password2`, `first_name` (opt), `last_name` (opt), `company_name` (opt, pour la société par défaut).
    *   **Response (201 CREATED)** : `{"user": <UserSerializer_data>, "token": "<token_value>", "default_company": <CompanySerializer_data>}`.
    *   **Erreurs (400 BAD REQUEST)** : Champs manquants, email/username déjà utilisé, mots de passe non identiques.
*   **`POST /api/users/login/`**
    *   **Description** : Connexion d'un utilisateur.
    *   **Permissions** : `AllowAny`.
    *   **Request Body** (`AuthTokenSerializer` de DRF) : `username`, `password`.
    *   **Response (200 OK)** : `{"token": "<token_value>", "user_id": <id>, "username": "...", "email": "..."}`.
    *   **Erreurs (400 BAD REQUEST)** : Identifiants incorrects, compte inactif.
*   **`GET /api/users/me/`**
    *   **Description** : Récupérer les informations de l'utilisateur actuellement authentifié.
    *   **Permissions** : `IsAuthenticated`.
    *   **Response (200 OK)** : `UserSerializer` data.
*   **`PUT /api/users/me/` / `PATCH /api/users/me/`**
    *   **Description** : Mettre à jour les informations de l'utilisateur (ex: email, prénom, nom). Ne permet pas de changer le mot de passe ici.
    *   **Permissions** : `IsAuthenticated`.
    *   **Request Body** (`UserSerializer` partiel) : Champs modifiables.
    *   **Response (200 OK)** : `UserSerializer` data mise à jour.
*   **`POST /api/users/logout/` (Si implémenté côté serveur)**
    *   **Description** : Invalide le token d'authentification actuel.
    *   **Permissions** : `IsAuthenticated`.
    *   **Response (204 NO CONTENT ou 200 OK)**.
*   **`POST /api/users/password/change/`**
    *   **Description** : Changer le mot de passe de l'utilisateur authentifié.
    *   **Permissions** : `IsAuthenticated`.
    *   **Request Body** (`PasswordChangeSerializer` de DRF) : `old_password`, `new_password1`, `new_password2`.
    *   **Response (200 OK)** : `{"detail": "New password has been saved."}`.
*   **`POST /api/users/password/reset/`**
    *   **Description** : Initier la procédure de réinitialisation de mot de passe.
    *   **Permissions** : `AllowAny`.
    *   **Request Body** : `{"email": "<user_email>"}`.
    *   **Response (200 OK)** : `{"detail": "Password reset e-mail has been sent."}` (même si l'email n'existe pas, pour éviter l'énumération d'utilisateurs).
*   **`POST /api/users/password/reset/confirm/`**
    *   **Description** : Confirmer la réinitialisation du mot de passe avec un token reçu par email.
    *   **Permissions** : `AllowAny`.
    *   **Request Body** (`PasswordResetConfirmSerializer` de DRF) : `uid`, `token`, `new_password1`, `new_password2`.
    *   **Response (200 OK)** : `{"detail": "Password has been reset with the new password."}`.

#### 5.1.2. `Company` Endpoints (sous `/api/users/companies/`)

*   **`GET /api/users/companies/`**
    *   **Description** : Lister les sociétés appartenant à l'utilisateur authentifié.
    *   **Permissions** : `IsAuthenticated`.
    *   **Response (200 OK)** : Liste de `CompanySerializer` data.
*   **`POST /api/users/companies/`**
    *   **Description** : Créer une nouvelle société. L'utilisateur authentifié en devient propriétaire.
    *   **Permissions** : `IsAuthenticated`.
    *   **Request Body** (`CompanySerializer` sans `owner`) : `name`, `address` (opt), `logo` (opt).
    *   **Response (201 CREATED)** : `CompanySerializer` data de la nouvelle société.
*   **`GET /api/users/companies/<uuid:company_id>/`**
    *   **Description** : Détails d'une société.
    *   **Permissions** : `IsAuthenticated` + Permission personnalisée (être propriétaire).
    *   **Response (200 OK)** : `CompanySerializer` data.
*   **`PUT /api/users/companies/<uuid:company_id>/`**
    *   **Description** : Mettre à jour une société.
    *   **Permissions** : `IsAuthenticated` + Permission personnalisée (être propriétaire).
    *   **Request Body** (`CompanySerializer` sans `owner`).
    *   **Response (200 OK)** : `CompanySerializer` data mise à jour.
*   **`DELETE /api/users/companies/<uuid:company_id>/`**
    *   **Description** : Supprimer une société. Action destructive.
    *   **Permissions** : `IsAuthenticated` + Permission personnalisée (être propriétaire).
    *   **Response (204 NO CONTENT)**.

### 5.2. Module Clients (`/api/clients/`)

Voir `03_clients_gestion.md`. Les endpoints sont des `ModelViewSet` standard pour le modèle `Client`.
La permission clé ici est de s'assurer que le client est bien rattaché à une `company_account` à laquelle l'utilisateur a accès (typiquement, la société active sélectionnée ou une société qu'il possède).

*   **`GET /api/clients/`**
    *   **Query Params** : `company_account_id` (requis, pour filtrer par la société active), `search` (nom, email), `ordering`, `page`.
    *   **Response** : Liste paginée de `ClientSerializer` data.
*   **`POST /api/clients/`**
    *   **Request Body** (`ClientSerializer`) : Doit inclure `company_account` (ID de la société active).
*   **`GET /api/clients/<uuid:client_id>/`**
*   **`PUT /api/clients/<uuid:client_id>/`**
*   **`PATCH /api/clients/<uuid:client_id>/`**
*   **`DELETE /api/clients/<uuid:client_id>/`**

### 5.3. Module Produits (`/api/products/`)

Voir `04_produits_gestion.md`. `ModelViewSet` pour `Product` et `ProductCategory`.
Permissions similaires au module Clients (basées sur `company_account`).

#### 5.3.1. `ProductCategory` Endpoints (sous `/api/products/categories/`)

*   **`GET /api/products/categories/`**
    *   **Query Params** : `company_account_id` (requis).
*   **`POST /api/products/categories/`**
    *   **Request Body** (`ProductCategorySerializer`) : `company_account` requis.
*   Autres : `GET <id>`, `PUT <id>`, `DELETE <id>`.

#### 5.3.2. `Product` Endpoints (sous `/api/products/`)

*   **`GET /api/products/`**
    *   **Query Params** : `company_account_id` (requis), `category_id`, `search` (nom, référence), `is_active`, `ordering`, `page`.
*   **`POST /api/products/`**
    *   **Request Body** (`ProductSerializer`) : `company_account` requis.
*   Autres : `GET <id>`, `PUT <id>`, `PATCH <id>`, `DELETE <id>`.

### 5.4. Module Documents (`/api/documents/`)

Voir `05_documents_gestion.md`. `ModelViewSet` pour `Document`.
La création (`POST`) et la mise à jour (`PUT`) d'un document accepteront des données imbriquées pour les `DocumentItem` via le `DocumentSerializer`.

*   **`GET /api/documents/`**
    *   **Query Params** : `company_account_id` (requis), `client_id`, `document_type`, `status`, `issue_date_after`, `issue_date_before`, `ordering`, `page`.
*   **`POST /api/documents/`**
    *   **Request Body** (`DocumentSerializer`) :
        *   `company_account` (ID de la société active).
        *   `client` (ID du client).
        *   `document_type`.
        *   `items` (liste d'objets `DocumentItemSerializer` data).
        *   Autres champs du document.
    *   **Logique Interne** : Génération de `document_reference`, calcul des totaux.
*   **`GET /api/documents/<uuid:document_id>/`**
    *   **Response** : `DocumentSerializer` data, incluant les `items` imbriqués.
*   **`PUT /api/documents/<uuid:document_id>/`**
    *   Principalement pour les documents en statut `DRAFT`. Modification des items possible.
*   **`PATCH /api/documents/<uuid:document_id>/`**
    *   Pour des modifications partielles, notamment le changement de `status`.
    *   Ex: `{"status": "SENT"}`.
*   **`DELETE /api/documents/<uuid:document_id>/`**
    *   Généralement permis uniquement pour les documents en statut `DRAFT`.
*   **`GET /api/documents/<uuid:document_id>/download_pdf/`**
    *   **Description** : Génère et retourne le document au format PDF.
    *   **Permissions** : `IsAuthenticated` + accès au document.
    *   **Response** : Fichier PDF (`Content-Type: application/pdf`).
    *   **Logique Interne** : Utilisation de templates HTML + convertisseur PDF (ex: WeasyPrint).

## 6. Conventions de Nommage et Structure des Réponses

*   **Nommage des Champs** : `snake_case` en JSON (DRF le fait par défaut si les modèles utilisent `snake_case`).
*   **Réponses de Liste (GET)** :
    ```json
    {
        "count": 100, // Nombre total d'items
        "next": "/api/resource/?page=3", // URL de la page suivante (ou null)
        "previous": "/api/resource/?page=1", // URL de la page précédente (ou null)
        "results": [
            { /* objet ressource 1 */ },
            { /* objet ressource 2 */ }
        ]
    }
    ```
*   **Réponses de Détail (GET <id>) / Création (POST) / Mise à Jour (PUT/PATCH)** :
    ```json
    {
        /* objet ressource complet */
    }
    ```
*   **Réponses d'Erreur (400 BAD REQUEST - Validation)** :
    ```json
    {
        "field_name": ["Error message 1 for this field.", "Error message 2."],
        "non_field_errors": ["General error message."]
    }
    ```
*   **Réponses d'Erreur (Autres 4xx, 5xx)** :
    ```json
    {
        "detail": "Error message."
    }
    ```

---
Ce document de spécification API est fondamental. Il sera la "source de vérité" pour les interactions entre le frontend et le backend. Il devra être maintenu à jour au fur et à mesure que de nouvelles fonctionnalités sont ajoutées ou que des modifications sont apportées.
Les serializers et vues spécifiques seront codés dans leurs applications Django respectives, mais ce document sert de vue d'ensemble et de contrat.
