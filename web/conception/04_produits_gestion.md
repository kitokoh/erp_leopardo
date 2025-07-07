# Module : Gestion des Produits

## 1. Introduction et Objectifs

Ce module permet la gestion du catalogue de produits ou services offerts par la société. Ces produits seront ensuite utilisés lors de la création de documents commerciaux (proformas, factures, devis). Chaque produit est rattaché à une "Société" (compte entreprise) spécifique.

**Objectifs Clés :**

*   Permettre la création de nouveaux produits ou services.
*   Gérer des catégories de produits.
*   Afficher une liste paginée et filtrable des produits.
*   Permettre la consultation détaillée des informations d'un produit.
*   Permettre la modification des informations d'un produit.
*   Permettre la suppression (ou désactivation) d'un produit.
*   Associer les produits à la société active de l'utilisateur.

## 2. Modèles de Données Associés

*   **`products.ProductCategory`** (Défini dans `00_architecture_globale.md`)
    *   `id`, `created_at`, `updated_at` (de `TimeStampedModel`)
    *   `company_account = models.ForeignKey(Company, related_name='product_categories', on_delete=models.CASCADE)`
    *   `name = models.CharField(max_length=200)`
    *   `description = models.TextField(blank=True, null=True)`
*   **`products.Product`** (Défini dans `00_architecture_globale.md`)
    *   `id`, `created_at`, `updated_at` (de `TimeStampedModel`)
    *   `company_account = models.ForeignKey(Company, related_name='products', on_delete=models.CASCADE)`
    *   `category = models.ForeignKey(ProductCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)`
    *   `name = models.CharField(max_length=255)`
    *   `reference = models.CharField(max_length=100, null=True, blank=True)` (Potentiellement unique par `company_account`)
    *   `description = models.TextField(null=True, blank=True)`
    *   `unit_price = models.DecimalField(max_digits=10, decimal_places=2)` (Prix unitaire HT)
    *   `is_active = models.BooleanField(default=True)` : Pour désactiver un produit.
    *   `product_type = models.CharField(max_length=50, choices=[('GOODS', 'Bien'), ('SERVICE', 'Service')], default='GOODS')` (Optionnel)
    *   `unit_of_measure = models.CharField(max_length=50, null=True, blank=True)` (ex: "pièce", "heure", "kg") (Optionnel)
*   **`users.Company`** : La société propriétaire du catalogue de produits.
*   **`documents.DocumentItem`** : Les produits seront liés aux lignes des documents.

## 3. Spécifications de l'API (Endpoints DRF pertinents)

Détails dans `06_api_specifications_drf.md`. Résumé pour les produits et catégories :

*   **Catégories de Produits :**
    *   `GET /api/products/categories/`
    *   `POST /api/products/categories/`
    *   `GET /api/products/categories/<category_id>/`
    *   `PUT /api/products/categories/<category_id>/`
    *   `DELETE /api/products/categories/<category_id>/`
*   **Produits :**
    *   `GET /api/products/` : Lister tous les produits de la société active. Permet filtrage (par catégorie, nom) et pagination.
    *   `POST /api/products/` : Créer un nouveau produit pour la société active.
    *   `GET /api/products/<product_id>/` : Récupérer les détails d'un produit.
    *   `PUT /api/products/<product_id>/` : Mettre à jour un produit.
    *   `DELETE /api/products/<product_id>/` : Supprimer un produit.

L'API s'assurera que toutes les opérations sont effectuées dans le contexte de la `company_account` de l'utilisateur.

## 4. Fonctionnalités Détaillées (Produits)

Les fonctionnalités pour les `ProductCategory` suivront un schéma CRUD similaire mais simplifié (principalement nom et description). Nous nous concentrons ici sur les `Product`.

### 4.1. Créer un Nouveau Produit

*   **Cas d'Utilisation (User Story)** : "En tant que gestionnaire de catalogue, je veux ajouter un nouveau produit ou service avec ses détails (nom, référence, description, prix) pour l'utiliser dans mes documents commerciaux."
*   **Préconditions** : Utilisateur connecté, société active sélectionnée, droits de création de produits.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur "Nouveau Produit" depuis la liste des produits.
    2.  **Interface Utilisateur (Page `/products/add/`)** :
        *   **URL** : `/products/add/`
        *   **Template** : `products/product_form.html`
        *   **Formulaire** (basé sur `products.forms.ProductForm`):
            *   Champ "Nom du produit" (`name`): Texte, requis.
            *   Champ "Référence" (`reference`): Texte, optionnel.
            *   Champ "Catégorie" (`category`): Select (liste des `ProductCategory` de la société active, chargées via API/contexte).
            *   Champ "Description" (`description`): Textarea, optionnel.
            *   Champ "Prix Unitaire (HT)" (`unit_price`): Nombre décimal, requis.
            *   (Optionnel) Champ "Type de produit" (`product_type`): Select (Bien/Service).
            *   (Optionnel) Champ "Unité de mesure" (`unit_of_measure`): Texte.
            *   Bouton "Enregistrer le produit".
    3.  **Logique Backend (Vue Django `products.views.ProductCreateView`)** :
        *   `GET` : Récupère les catégories de produits pour la société active (via API `GET /api/products/categories/`) pour peupler le champ `category`. Affiche le formulaire `ProductForm`.
        *   `POST` :
            *   Récupère `active_company_id`.
            *   Valide `ProductForm`.
            *   Si valide : Prépare payload JSON (incluant `company_account: active_company_id`), appelle `POST /api/products/`.
            *   Si succès API : Message de succès, redirection vers liste des produits ou détail du nouveau produit.
            *   Si erreur : Ré-affiche formulaire avec erreurs.
*   **Postconditions** : Nouveau `Product` créé, associé à la `company_account` active.
*   **Permissions Requises** : Authentifié, droits de gestion de produits.

### 4.2. Afficher la Liste des Produits

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux voir la liste des produits/services de ma société active pour les consulter ou les sélectionner."
*   **Préconditions** : Utilisateur connecté, société active sélectionnée.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur menu "Produits".
    2.  **Interface Utilisateur (Page `/products/`)** :
        *   **URL** : `/products/`
        *   **Template** : `products/product_list.html`
        *   **Affichage** :
            *   Titre : "Catalogue des Produits (Société : [Nom société active])".
            *   Bouton "Ajouter un Produit", "Gérer les Catégories".
            *   **Zone de Filtres/Recherche (HTMX)** :
                *   Recherche par nom/référence.
                *   Filtre par `ProductCategory`.
                *   Filtre par statut (`is_active`).
            *   **Tableau des Produits** (`<div id="product-table-container">...</div>` pour HTMX) :
                *   Colonnes : Nom, Référence, Catégorie, Prix Unitaire, Statut.
                *   Actions : Modifier, Supprimer/Désactiver.
            *   **Pagination**.
    3.  **Logique Backend (Vue Django `products.views.ProductListView`)** :
        *   `GET` : Récupère `active_company_id`. Récupère filtres/page. Appelle `GET /api/products/` (avec `company_account`, filtres). Récupère aussi les catégories (pour le filtre) via `GET /api/products/categories/`.
        *   Passe produits, pagination, catégories, filtres actifs au template.
        *   Si requête HTMX : Rend fragment de tableau.
*   **Interactions HTMX/Alpine.js** : Recherche, filtres, pagination via HTMX.
*   **Postconditions** : Liste des produits affichée.
*   **Permissions Requises** : Authentifié, droits de lecture produits.

### 4.3. Consulter les Détails d'un Produit

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux voir toutes les informations d'un produit spécifique."
*   **Préconditions** : Utilisateur connecté, accès au produit (produit de sa société active).
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur nom d'un produit dans la liste.
    2.  **Interface Utilisateur (Page `/products/<product_id>/`)** :
        *   **URL** : `/products/<uuid:product_id>/`
        *   **Template** : `products/product_detail.html`
        *   **Affichage** :
            *   Titre : "Détail du Produit : [Nom produit]".
            *   Boutons : "Modifier", "Supprimer/Désactiver".
            *   **Informations** : Nom, Référence, Catégorie, Description, Prix Unitaire, Statut, Type, Unité de mesure.
            *   (Optionnel) Historique de prix, documents où il est utilisé.
    3.  **Logique Backend (Vue Django `products.views.ProductDetailView`)** :
        *   `GET` : Récupère `product_id`, `active_company_id`. Appelle `GET /api/products/<product_id>/`.
        *   Passe l'objet produit au template.
*   **Postconditions** : Détails du produit affichés.
*   **Permissions Requises** : Authentifié, droits de lecture produit.

### 4.4. Modifier un Produit Existant

*   **Cas d'Utilisation (User Story)** : "En tant que gestionnaire de catalogue, je veux modifier les informations d'un produit existant."
*   **Préconditions** : Utilisateur connecté, droits de modification sur le produit.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur "Modifier" depuis liste ou détail produit.
    2.  **Interface Utilisateur (Page `/products/<product_id>/edit/`)** :
        *   **URL** : `/products/<uuid:product_id>/edit/`
        *   **Template** : `products/product_form.html`
        *   **Formulaire** : `ProductForm` pré-rempli avec données actuelles.
            *   Bouton "Enregistrer les modifications".
    3.  **Logique Backend (Vue Django `products.views.ProductUpdateView`)** :
        *   `GET` : Récupère produit via API, initialise `ProductForm` (avec catégories pour le select). Affiche formulaire.
        *   `POST` : Valide `ProductForm`. Si valide, appelle `PUT /api/products/<product_id>/` avec données modifiées.
        *   Si succès API : Message, redirection vers détail produit.
        *   Si erreur : Ré-affiche formulaire avec erreurs.
*   **Postconditions** : `Product` mis à jour.
*   **Permissions Requises** : Authentifié, droits de modification produit.

### 4.5. Supprimer / Désactiver un Produit

*   **Cas d'Utilisation (User Story)** : "En tant que gestionnaire, je veux supprimer un produit obsolète ou le désactiver temporairement."
*   **Préconisation** : Préférer la désactivation (`is_active=False`) à la suppression physique pour maintenir l'intégrité des anciens documents utilisant ce produit. La suppression physique serait une action "super admin" avec plus de confirmations.
*   **Flux Nominal (Désactivation)** :
    1.  **Déclencheur** : Clic sur "Désactiver" (ou "Activer" si déjà inactif).
    2.  **Interface Utilisateur** : Confirmation via modale.
    3.  **Logique Backend (Action HTMX ou Vue Django)** :
        *   Sur confirmation, envoi `PATCH /api/products/<product_id>/` avec `{"is_active": false}` (ou `true`).
        *   L'API met à jour le champ.
        *   Message de succès, mise à jour de l'affichage du produit (statut, style).
*   **Flux Nominal (Suppression Physique - si implémenté)** :
    1.  **Déclencheur** : Clic sur "Supprimer définitivement" (après une première étape de désactivation ou dans une section "archivés").
    2.  **Interface Utilisateur (Page `/products/<product_id>/delete/` ou Modale)** : Confirmation explicite des conséquences.
    3.  **Logique Backend (Vue Django `products.views.ProductDeleteView`)** :
        *   `POST` : Appelle `DELETE /api/products/<product_id>/`.
        *   Si succès : Message, redirection vers liste des produits.
*   **Postconditions** : Produit désactivé ou supprimé.
*   **Permissions Requises** : Authentifié, droits de suppression/modification produit.

### 4.6. Gestion des Catégories de Produits (CRUD simplifié)

Les fonctionnalités CRUD pour `ProductCategory` (création, liste, modification, suppression) suivront un schéma très similaire à celui des produits, mais avec des formulaires et des vues plus simples (principalement gestion des champs `name` et `description`).

*   **Interface Utilisateur (Pages `/products/categories/`, `/products/categories/add/`, etc.)** :
    *   Liste des catégories avec nombre de produits dans chacune.
    *   Formulaires pour ajouter/modifier une catégorie.
*   **Logique Backend (Vues Django pour `ProductCategory`)** :
    *   Interactions avec les endpoints API `/api/products/categories/...`.

---
Ce module est crucial pour alimenter les documents commerciaux. Une bonne structuration des catégories et des informations produits facilitera grandement le travail des utilisateurs.
