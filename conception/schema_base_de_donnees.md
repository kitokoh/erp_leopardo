# Schéma de la Base de Données

Ce document décrit la structure de la base de données utilisée par l'application Client Document Manager. L'application utilise SQLAlchemy comme ORM (Object-Relational Mapper) et est configurée par défaut pour utiliser une base de données SQLite.

Pour une description des modèles SQLAlchemy existants, référez-vous au document `cahier/desktop/structure_base_de_donnees.md` qui a été produit lors de l'analyse initiale. Ce document de conception s'appuiera sur cette analyse et la formalisera.

## 1. Technologie et Configuration

*   **ORM**: SQLAlchemy. Les modèles sont définis comme des classes Python héritant de `Base` (déclarative_base).
*   **Base de Données par Défaut**: SQLite (fichier `client_manager_app.db`).
*   **Localisation des Modèles**: Principalement dans le dossier `db/models/`.
*   **Initialisation**: Le schéma est créé au démarrage de l'application via `db.init_schema.initialize_database()`.
*   **Données Initiales (Seed)**: Des données initiales peuvent être peuplées via `db.db_seed.run_seed()`.

## 2. Diagramme Entité-Relation (Simplifié)

Un diagramme Entité-Relation (ERD) complet serait très vaste. Voici une tentative de représenter les relations entre les entités les plus critiques. Pour un diagramme visuel, se référer à `conception/diagrammes/schema_bdd_simplifie.png` (qui sera un placeholder pour un diagramme généré).

```mermaid
erDiagram
    USERS ||--o{ AUTH_SESSIONS : "has"
    USERS {
        Integer id PK
        String username
        String hashed_password
        String email
        String role
        Boolean is_active
        DateTime created_at
    }

    CLIENTS ||--o{ CONTACTS : "has"
    CLIENTS ||--o{ PROJECTS : "manages"
    CLIENTS ||--o{ INVOICES : "receives"
    CLIENTS ||--o{ PROFORMA_INVOICES : "receives"
    CLIENTS ||--o{ CLIENT_DOCUMENTS : "has"
    CLIENTS {
        Integer id PK
        String company_name
        String project_identifier
        String contact_person
        String email
        String phone
        String address
        String status
        DateTime created_at
    }

    CONTACTS {
        Integer id PK
        Integer client_id FK
        String name
        String email
        String phone
        String role
    }

    PRODUCTS {
        Integer id PK
        String name
        String reference
        String description
        Float price
        String unit
        Integer category_id FK
        DateTime created_at
    }

    PROJECTS ||--o{ PROJECT_FILES : "contains"
    PROJECTS ||--o{ PROJECT_LOGS : "logs"
    PROJECTS ||--o{ MILESTONES : "has"
    PROJECTS {
        Integer id PK
        Integer client_id FK
        String name
        String description
        String status
        Date start_date
        Date end_date
    }

    INVOICES ||--o{ INVOICE_LINES : "contains"
    INVOICES {
        Integer id PK
        Integer client_id FK
        String invoice_number
        Date issue_date
        Date due_date
        Float total_amount
        String status (e.g., 'draft', 'sent', 'paid')
    }

    INVOICE_LINES {
        Integer id PK
        Integer invoice_id FK
        Integer product_id FK
        String description
        Integer quantity
        Float unit_price
        Float total_price
    }

    PROFORMA_INVOICES ||--o{ PROFORMA_INVOICE_LINES : "contains"
    PROFORMA_INVOICES {
        Integer id PK
        Integer client_id FK
        String proforma_number
        Date issue_date
        Float total_amount
    }

    PROFORMA_INVOICE_LINES {
        Integer id PK
        Integer proforma_invoice_id FK
        Integer product_id FK
        String description
        Integer quantity
        Float unit_price
        Float total_price
    }

    TEMPLATES {
        Integer id PK
        String name
        String type -- e.g., 'proforma', 'contract', 'packing_list'
        String language
        String file_path
        Boolean is_default
    }

    DOCUMENTS { -- Table générique ou ensemble de tables spécifiques
        Integer id PK
        String name
        String type -- ex: 'pdf', 'docx'
        String file_path
        Integer client_id FK "Optionnel, si lié à un client"
        Integer project_id FK "Optionnel, si lié à un projet"
        DateTime created_at
    }

    CLIENT_DOCUMENTS { -- Table de liaison si un document peut appartenir à plusieurs contextes ou pour métadonnées
        Integer id PK
        Integer client_id FK
        Integer document_id FK
        String document_type_for_client -- ex: 'Contrat Signé', 'Spécification Validée'
        String notes
    }

    EMPLOYEES {
        Integer id PK
        String first_name
        String last_name
        String email
        String phone
        String position
        Integer user_id FK "Lien vers la table USERS si l'employé est un utilisateur"
    }

    RECRUITMENT_JOB_OPENINGS {
        Integer id PK
        String title
        String description
        String status
    }

    RECRUITMENT_CANDIDATES ||--o{ RECRUITMENT_INTERVIEWS : "has"
    RECRUITMENT_CANDIDATES {
        Integer id PK
        Integer job_opening_id FK
        String first_name
        String last_name
        String email
        String phone
        String status
    }

    APPLICATION_SETTINGS {
        Integer id PK
        String key UK
        String value
        String description
    }

    COMPANIES { -- Informations sur l'entreprise qui utilise l'application
        Integer id PK
        String name
        String address
        String phone
        String email
        String logo_path
        String tax_id
    }

    USERS ||--o{ EMPLOYEES : "can be"
    PRODUCTS }o--o{ PRODUCT_CATEGORIES : "belongs to"
    INVOICE_LINES }o--|| PRODUCTS : "references"
    PROFORMA_INVOICE_LINES }o--|| PRODUCTS : "references"
```

**Note sur le diagramme Mermaid :** Ce diagramme est une simplification et peut ne pas représenter toutes les tables ni toutes les relations exactes du projet réel. Il vise à donner une idée générale. Les noms de tables sont en majuscules pour correspondre à une convention ERD courante, bien que les modèles SQLAlchemy soient typiquement en `CamelCase` et les tables générées en `snake_case`.

## 3. Description des Tables Principales (Basée sur `cahier/desktop/structure_base_de_donnees.md`)

La documentation existante dans `cahier/desktop/structure_base_de_donnees.md` liste de nombreux modèles. Voici un résumé des groupes d'entités les plus importants :

### 3.1. Utilisateurs et Accès (`users`, `roles`, `permissions`)
*   **`users`**: Stocke les informations des utilisateurs de l'application, y compris les identifiants de connexion, le mot de passe haché, l'e-mail et le rôle associé.
    *   Colonnes clés : `id`, `username`, `hashed_password`, `email`, `role`, `is_active`, `created_at`.
*   **`roles`** (implicite ou explicite) : Définit les rôles des utilisateurs (ex: 'admin', 'user', 'sales').
*   **`permissions`** (implicite ou explicite) : Définit les actions permises pour chaque rôle.

### 3.2. Clients et Contacts (`clients`, `contacts`, `client_assigned_personnel`, etc.)
*   **`clients`**: Informations détaillées sur les entreprises clientes.
    *   Colonnes clés : `id`, `company_name`, `project_identifier`, `status`, `address`, `contact_details`.
*   **`contacts`**: Personnes de contact associées aux clients.
    *   Colonnes clés : `id`, `client_id` (FK), `name`, `email`, `phone`.
*   Tables de liaison pour documents clients, transitaires, agents de transfert, etc.

### 3.3. Produits et Stock (`products`, `internal_stock_items`, `item_locations`)
*   **`products`**: Catalogue des produits et services offerts.
    *   Colonnes clés : `id`, `name`, `reference`, `description`, `price`, `unit`, `category_id`.
*   **`internal_stock_items`**: Gestion des articles en stock.
*   **`item_locations`**: Localisation des articles en stock.

### 3.4. Documents et Modèles (`proforma_invoices`, `invoices`, `templates`, `cover_pages`)
*   **`proforma_invoices`**, **`invoices`**: Tables pour les factures proforma et finales, avec des détails tels que le numéro, les dates, le montant total, le statut, et une référence au client.
    *   Chacune est liée à des tables de lignes (ex: `proforma_invoice_lines`, `invoice_lines`) qui détaillent les produits/services inclus, leurs quantités et prix.
*   **`templates`**: Références aux fichiers modèles de documents (XLSX, DOCX, HTML) utilisés pour la génération.
    *   Colonnes clés : `id`, `name`, `type`, `language`, `file_path`, `is_default`.
*   **`cover_pages`**, **`cover_page_templates`**: Gestion des pages de garde.

### 3.5. Projets (`projects`, `tasks`, `milestones`, `project_files`)
*   **`projects`**: Informations sur les projets gérés.
    *   Colonnes clés : `id`, `client_id` (FK), `name`, `status`, `start_date`, `end_date`.
*   **`tasks`**, **`milestones`**: Tâches et jalons associés aux projets.
*   **`project_files`**: Fichiers liés aux projets.

### 3.6. Recrutement (`recruitment_job_openings`, `recruitment_candidates`, `recruitment_interviews`)
*   **`recruitment_job_openings`**: Offres d'emploi.
*   **`recruitment_candidates`**: Informations sur les candidats.
*   **`recruitment_interviews`**: Suivi des entretiens.

### 3.7. RH et Employés (`employees`, `employee_documents`, `leave`, `performance`)
*   **`employees`**: Informations sur les employés de l'entreprise.
    *   Colonnes clés : `id`, `first_name`, `last_name`, `email`, `position`, `user_id` (FK vers `users` si l'employé est un utilisateur).
*   Tables pour les documents des employés, les congés, le suivi de la performance.

### 3.8. Finances et Comptabilité (Entreprise) (`company_expenses`, `company_assets`, `payments`)
*   **`company_expenses`**: Dépenses de l'entreprise.
*   **`company_assets`**: Actifs de l'entreprise.
*   **`payments`**: Paiements reçus des clients.

### 3.9. Paramètres et Divers (`application_settings`, `companies`, `locations`, `media_items`)
*   **`application_settings`**: Stockage clé-valeur pour les paramètres de configuration de l'application.
*   **`companies`**: Informations sur l'entreprise (ou les entreprises) utilisant l'application.
*   **`locations`**: Adresses, sites.
*   **`media_items`**: Référentiel central pour les fichiers médias.

## 4. Relations Clés

*   **Clés Primaires (PK)**: Généralement une colonne `id` (Integer, auto-incrémentée) pour chaque table.
*   **Clés Étrangères (FK)**: Utilisées pour établir des relations entre les tables (ex: `invoices.client_id` référence `clients.id`).
*   **Types de Relations**:
    *   **One-to-Many**: Un client peut avoir plusieurs factures. Un projet peut avoir plusieurs tâches.
    *   **Many-to-One**: Plusieurs factures peuvent appartenir à un seul client.
    *   **Many-to-Many**: Souvent implémentées avec une table associative (ex: une table `project_members` pour lier `projects` et `users`). Les produits dans une facture (via `invoice_lines`) est un exemple de relation many-to-many entre `invoices` et `products`.
*   **Cascading**: SQLAlchemy permet de définir des règles de cascade pour les opérations `DELETE` et `UPDATE` (ex: supprimer toutes les factures d'un client si le client est supprimé). Celles-ci doivent être définies avec soin.

## 5. Indexation

Pour garantir des performances optimales, des index devraient être créés sur :

*   Les clés primaires (automatiquement par la plupart des SGBD).
*   Les clés étrangères.
*   Les colonnes fréquemment utilisées dans les clauses `WHERE` des requêtes (ex: `clients.company_name`, `products.reference`, `invoices.status`).
*   Les colonnes utilisées pour le tri (`ORDER BY`).

SQLAlchemy permet de spécifier les index lors de la définition des modèles.

## 6. Considérations

*   **Intégrité Référentielle**: Assurée par l'utilisation correcte des clés étrangères et des contraintes.
*   **Normalisation**: Le schéma semble viser un bon niveau de normalisation pour éviter la redondance des données.
*   **Évolutivité du Schéma**: Pour les modifications futures du schéma, un outil de migration de base de données comme Alembic (couramment utilisé avec SQLAlchemy) est fortement recommandé pour gérer les changements de manière versionnée et reproductible. Sa présence actuelle n'est pas confirmée mais serait une bonne pratique.
*   **Types de Données**: Utilisation de types de données appropriés pour chaque colonne (Integer, String, Float, DateTime, Boolean, etc.).

Ce document, combiné à l'exploration directe des fichiers modèles dans `db/models/`, fournit une base solide pour comprendre la structure de persistance des données de l'application. Les CRUDs dans `db/cruds/` montrent comment ces modèles sont manipulés.
