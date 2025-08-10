# Module : Gestion des Sociétés (Comptes Entreprise)

## 1. Introduction et Objectifs

Ce module gère les entités "Société" (ou "Compagnie" / "Compte Entreprise"). Dans le contexte de cette application, une société est l'entité principale à laquelle toutes les autres données métier (clients, produits, documents, etc.) sont rattachées. Un utilisateur peut être propriétaire ou membre de plusieurs sociétés, mais agira généralement dans le contexte d'UNE société active à la fois.

**Objectifs Clés :**

*   Permettre à un utilisateur de créer une nouvelle société.
*   Permettre à un utilisateur de voir la liste des sociétés auxquelles il a accès (celles qu'il possède ou dont il est membre).
*   Permettre à un utilisateur de sélectionner une "société active" pour sa session de travail.
*   Permettre au propriétaire d'une société d'en modifier les informations.
*   (Plus tard) Permettre au propriétaire d'inviter d'autres utilisateurs à rejoindre sa société avec des rôles spécifiques.
*   (Plus tard) Permettre à un utilisateur de quitter une société.

## 2. Modèles de Données Associés

*   **`users.Company`** (Défini dans `00_architecture_globale.md` et rappelé ici)
    *   `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
    *   `created_at = models.DateTimeField(auto_now_add=True)`
    *   `updated_at = models.DateTimeField(auto_now=True)`
    *   `name = models.CharField(max_length=255)` : Nom de la société.
    *   `address = models.TextField(null=True, blank=True)` : Adresse.
    *   `logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)` : Logo.
    *   `owner = models.ForeignKey(User, related_name='owned_companies', on_delete=models.CASCADE)` : L'utilisateur qui a créé et possède la société.
    *   `is_active_for_owner = models.BooleanField(default=True)`: Optionnel, pour marquer si c'est la société par défaut/active pour le propriétaire. Une autre approche serait de stocker la société active en session ou dans un modèle UserProfile.
    *   Autres champs potentiels : `siret`, `vat_number`, `phone`, `email_contact`, `website`.
*   **`users.User`** (Modèle Django `AbstractUser` étendu)
    *   Lien via `owner` dans `Company`.
*   **(Potentiel futur) `users.Membership`** (Si gestion fine des membres et rôles par société)
    *   `user = models.ForeignKey(User, on_delete=models.CASCADE)`
    *   `company = models.ForeignKey(Company, on_delete=models.CASCADE)`
    *   `role = models.CharField(max_length=50)` (ex: 'admin', 'editor', 'viewer')
    *   `date_joined = models.DateTimeField(auto_now_add=True)`

**Note sur la "Société Active"**:
Pour le MVP, on peut simplifier : un utilisateur crée une société lors de son inscription, et c'est sa société active par défaut. S'il crée d'autres sociétés, un mécanisme pour basculer entre elles sera nécessaire. Ce mécanisme pourrait être un simple menu déroulant dans la barre de navigation qui met à jour une variable de session (`active_company_id`). Toutes les opérations CRUD (Clients, Produits, Documents) se feront alors dans le contexte de cette `active_company_id`. L'API devra aussi prendre en compte cette société active pour filtrer les données.

## 3. Spécifications de l'API (Endpoints DRF pertinents)

Détails dans `06_api_specifications_drf.md`. Résumé :

*   **`GET /api/users/companies/`** : Lister les sociétés appartenant à l'utilisateur authentifié.
*   **`POST /api/users/companies/`** : Créer une nouvelle société pour l'utilisateur authentifié.
*   **`GET /api/users/companies/<company_id>/`** : Récupérer les détails d'une société spécifique (si l'utilisateur en est propriétaire).
*   **`PUT /api/users/companies/<company_id>/`** : Mettre à jour une société.
*   **`DELETE /api/users/companies/<company_id>/`** : Supprimer une société (avec précautions).
*   **`POST /api/users/companies/<company_id>/set_active/` (Optionnel)** : Endpoint pour définir une société comme active pour l'utilisateur.

## 4. Fonctionnalités Détaillées

### 4.1. Création d'une Nouvelle Société (Post-Inscription)

*   **Contexte** : Un utilisateur peut vouloir créer d'autres sociétés après sa société initiale créée à l'inscription.
*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur connecté, je veux créer une nouvelle entité société pour gérer séparément les affaires d'une autre entreprise ou filiale."
*   **Préconditions** : L'utilisateur est connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur clique sur un bouton "Créer une nouvelle société" (ex: dans une page de gestion de compte/sociétés, ou un menu déroulant listant ses sociétés).
    2.  **Interface Utilisateur (Page `/companies/add/`)** :
        *   **URL** : `/companies/add/`
        *   **Template** : `users/company_form.html` (un template générique pour création/édition)
        *   **Formulaire** (basé sur `users.forms.CompanyForm`):
            *   Champ "Nom de la société" (`name`): Texte, requis.
            *   Champ "Adresse" (`address`): Textarea, optionnel.
            *   Champ "Logo" (`logo`): File input, optionnel.
            *   (Autres champs du modèle `Company` si pertinents pour la création).
            *   Bouton "Créer la société".
    3.  **Logique Backend (Vue Django `users.views.CompanyCreateView`)** :
        *   Méthode `GET` : Affiche le formulaire `CompanyForm` vide.
        *   Méthode `POST` :
            *   Récupère les données du formulaire.
            *   Valide les données avec `CompanyForm`.
            *   Si valide :
                *   Appelle l'endpoint API `POST /api/users/companies/` avec les données. L'API (via `CompanySerializer` et `CompanyViewSet`) crée l'objet `Company` et l'associe à `request.user` comme `owner`.
                *   Si succès de l'API : Affiche un message de succès. Redirige vers la liste des sociétés ou la page de détail de la nouvelle société. Potentiellement, propose de définir cette nouvelle société comme active.
            *   Si invalide ou erreur API : Ré-affiche le formulaire avec les erreurs.
*   **Flux Alternatifs et Exceptions** :
    *   Nom de société potentiellement dupliqué (si une contrainte d'unicité est souhaitée par utilisateur) : L'API ou le modèle doit gérer cela.
    *   Erreur d'upload du logo.
*   **Postconditions** : Une nouvelle `Company` est créée et associée à l'utilisateur comme `owner`.
*   **Permissions Requises** : Utilisateur authentifié.

### 4.2. Liste des Sociétés de l'Utilisateur

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur connecté, je veux voir la liste de toutes les sociétés que je possède ou dont je suis membre pour pouvoir en sélectionner une."
*   **Préconditions** : L'utilisateur est connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur accède à une page "Mes Sociétés" ou via un menu déroulant de sélection de société.
    2.  **Interface Utilisateur (Page `/companies/`)** :
        *   **URL** : `/companies/`
        *   **Template** : `users/company_list.html`
        *   **Affichage** :
            *   Liste des sociétés : Pour chaque société, afficher le nom, peut-être l'adresse ou le logo.
            *   Indication de la société actuellement "active" (si ce concept est implémenté).
            *   Lien/bouton pour "Activer" une société (si pas active).
            *   Lien pour "Modifier" les détails de la société (si propriétaire).
            *   Lien pour "Voir les détails" ou "Accéder au tableau de bord" de cette société.
            *   Bouton "Créer une nouvelle société".
    3.  **Logique Backend (Vue Django `users.views.CompanyListView`)** :
        *   Méthode `GET` :
            *   Appelle l'endpoint API `GET /api/users/companies/`. L'API retourne la liste des sociétés liées à `request.user`.
            *   Récupère l'ID de la société active depuis la session de l'utilisateur (si implémenté).
            *   Passe la liste des sociétés et l'ID de la société active au template.
*   **Postconditions** : L'utilisateur voit la liste de ses sociétés.
*   **Permissions Requises** : Utilisateur authentifié.

### 4.3. Sélectionner une Société Active

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur ayant accès à plusieurs sociétés, je veux sélectionner l'une d'elles comme contexte de travail actif pour que toutes mes actions (création de clients, documents, etc.) soient rattachées à cette société."
*   **Préconditions** : L'utilisateur est connecté et a accès à au moins une société.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** :
        *   Option A : Depuis la `CompanyListView`, l'utilisateur clique sur un bouton "Activer" à côté d'une société.
        *   Option B : Un menu déroulant dans la barre de navigation principale liste les sociétés de l'utilisateur. Sélectionner une société dans ce menu.
    2.  **Interface Utilisateur** :
        *   L'action est un POST vers une URL spécifique ou un GET avec un paramètre.
        *   **URL (Exemple pour Option A)** : `/companies/<company_id>/set_active/`
    3.  **Logique Backend (Vue Django `users.views.SetActiveCompanyView`)** :
        *   Méthode `POST` ou `GET` :
            *   Récupère l'ID de la société à activer depuis l'URL ou les données POST.
            *   Vérifie que l'utilisateur a bien accès à cette société (est propriétaire ou membre). Cette vérification peut être faite en essayant de récupérer la société via l'API `GET /api/users/companies/<company_id>/` ou par une requête ORM directe si la vue a cette responsabilité.
            *   Si l'utilisateur a accès : Stocke `company_id` dans la session de l'utilisateur (ex: `request.session['active_company_id'] = company_id`).
            *   Optionnel : Appelle un endpoint API `POST /api/users/companies/<company_id>/set_active/` si la logique de "société active" doit aussi être persistée côté API/DB pour une raison quelconque (ex: pour des workers Celery qui auraient besoin de connaître la société active de l'utilisateur).
            *   Redirige l'utilisateur vers le tableau de bord (`/dashboard/`) ou la page d'où il venait, avec un message de succès. Le tableau de bord devrait maintenant refléter les données de la nouvelle société active.
*   **Flux Alternatifs et Exceptions** :
    *   L'utilisateur essaie d'activer une société à laquelle il n'a pas accès : Erreur 403 ou redirection avec message.
*   **Postconditions** : La session de l'utilisateur contient l'ID de la nouvelle société active. Les affichages subséquents de données (clients, produits, etc.) sont filtrés par cette société.
*   **Permissions Requises** : Utilisateur authentifié, doit avoir accès à la société cible.

### 4.4. Modification des Informations d'une Société

*   **Cas d'Utilisation (User Story)** : "En tant que propriétaire d'une société, je veux modifier ses informations (nom, adresse, logo, etc.)."
*   **Préconditions** : L'utilisateur est connecté et est propriétaire (`owner`) de la société qu'il souhaite modifier.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Depuis la liste des sociétés ou la page de détail d'une société, l'utilisateur clique sur "Modifier".
    2.  **Interface Utilisateur (Page `/companies/<company_id>/edit/`)** :
        *   **URL** : `/companies/<company_id>/edit/`
        *   **Template** : `users/company_form.html` (le même que pour la création, mais pré-rempli)
        *   **Formulaire** : `CompanyForm` pré-rempli avec les données actuelles de la société.
            *   Bouton "Enregistrer les modifications".
    3.  **Logique Backend (Vue Django `users.views.CompanyUpdateView`)** :
        *   Méthode `GET` :
            *   Récupère les données de la société via l'API `GET /api/users/companies/<company_id>/`.
            *   Initialise `CompanyForm` avec ces données.
            *   Affiche le formulaire.
        *   Méthode `POST` :
            *   Récupère les données du formulaire soumis.
            *   Valide avec `CompanyForm`.
            *   Si valide :
                *   Appelle l'endpoint API `PUT /api/users/companies/<company_id>/` avec les données modifiées.
                *   Si succès de l'API : Affiche un message de succès. Redirige vers la liste des sociétés ou la page de détail de la société.
            *   Si invalide ou erreur API : Ré-affiche le formulaire avec les erreurs.
*   **Flux Alternatifs et Exceptions** :
    *   L'utilisateur n'est pas le propriétaire : Erreur 403.
    *   La société n'existe pas : Erreur 404.
*   **Postconditions** : Les informations de la `Company` sont mises à jour.
*   **Permissions Requises** : Utilisateur authentifié, doit être `owner` de la société.

### 4.5. (Futur) Inviter des Utilisateurs à une Société

*   **Cas d'Utilisation** : "En tant que propriétaire d'une société, je veux inviter d'autres utilisateurs existants de la plateforme à rejoindre ma société avec un rôle spécifique (ex: admin de société, employé)."
*   Cette fonctionnalité nécessitera un modèle `Membership` et une logique d'invitation (potentiellement par email, avec un token d'invitation).
*   **Interface** : Un formulaire pour entrer l'email de l'utilisateur à inviter et sélectionner son rôle dans la société.
*   **API Endpoints** :
    *   `POST /api/users/companies/<company_id>/invitations/`
    *   `GET /api/invitations/<invitation_token>/` (pour que l'invité voie l'invitation)
    *   `POST /api/invitations/<invitation_token>/accept/`
    *   `POST /api/invitations/<invitation_token>/decline/`
*   Sera détaillé dans une phase ultérieure.

### 4.6. (Futur) Supprimer une Société

*   **Cas d'Utilisation** : "En tant que propriétaire d'une société, je veux pouvoir supprimer une société (et toutes ses données associées)."
*   **Attention** : Opération très destructive. Nécessite des confirmations multiples.
*   **API Endpoint** : `DELETE /api/users/companies/<company_id>/`
*   La suppression en cascade des clients, produits, documents liés à cette société sera gérée par la base de données si les `ForeignKey` sont configurées avec `on_delete=models.CASCADE`.
*   Sera détaillé dans une phase ultérieure.

---
Ce document établit les bases pour la gestion des sociétés. La notion de "société active" est centrale et devra être gérée de manière cohérente à travers toute l'application (session, contexte des vues, filtrage API).
