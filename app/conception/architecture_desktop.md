# Architecture Détaillée - Application Desktop

Ce document se concentre sur l'architecture interne de l'application de bureau Client Document Manager. Pour une vue d'ensemble incluant l'application mobile, veuillez consulter le document d'[Architecture Globale](./architecture_globale.md).

## 1. Vue d'Ensemble de l'Architecture Desktop

L'application desktop est une application client lourd développée en Python avec PyQt5. Elle suit une architecture en couches pour séparer les préoccupations et améliorer la maintenabilité. Elle intègre également un serveur API FastAPI pour une communication externe.

```mermaid
graph TD
    A[Utilisateur] --> B[Interface Utilisateur (PyQt5)];

    subgraph "Application Desktop ClientDocManager"
        B --> C{Logique de Présentation / Contrôleurs UI};
        C --> D[Logique Métier / Services Applicatifs];
        D --> E[Couche d'Accès aux Données (CRUDs SQLAlchemy)];
        E --> F[Base de Données (SQLite)];

        D --> G[Module de Génération de Documents];
        G --> E;
        G -- Utilise des modèles --> H[Système de Fichiers (Modèles .docx, .xlsx)];

        C --> I[Gestionnaire d'Authentification et Permissions];
        I --> E;

        D --> J[Services Utilitaires (Email, Notifications, etc.)];

        subgraph "Serveur API Intégré"
            K[API Endpoints (FastAPI)];
            K --> D;
            K --> I;
        end
    end

    L[Client Externe (ex: App Mobile)] -.-> K;

    style B fill:#cde,stroke:#333,stroke-width:2px
    style F fill:#dbf,stroke:#333,stroke-width:2px
    style K fill:#dec,stroke:#333,stroke-width:2px
    style H fill:#f9f,stroke:#333,stroke-width:1px
```

## 2. Couches de l'Application Desktop

### 2.1. Interface Utilisateur (UI) - Couche de Présentation

*   **Description**: Responsable de l'interaction directe avec l'utilisateur. Elle affiche les données et capture les entrées de l'utilisateur.
*   **Technologies**: PyQt5.
*   **Composants Clés**:
    *   `main_window.py` (`DocumentManager`): Fenêtre principale de l'application.
    *   Dossier `dialogs/`: Contient de nombreuses fenêtres de dialogue pour des actions spécifiques (ajout/édition de clients, produits, génération de documents, etc.).
    *   Widgets personnalisés (ex: `client_widget.py`, `home_page_widget.py`, `settings_page.py`).
    *   Utilisation de fichiers `.ui` (Qt Designer) et/ou création d'interfaces par code.
    *   Gestion des signaux et slots pour la communication entre widgets.
*   **Responsabilités**:
    *   Afficher les données de manière conviviale.
    *   Valider les entrées utilisateur de base (format, champs obligatoires).
    *   Transmettre les actions utilisateur à la couche de Logique de Présentation / Contrôleurs.
    *   Mettre à jour l'affichage en fonction des données reçues.

### 2.2. Logique de Présentation / Contrôleurs UI

*   **Description**: Agit comme un intermédiaire entre l'UI et la Logique Métier. Elle interprète les actions de l'UI, appelle les services appropriés de la couche métier et prépare les données pour l'affichage.
*   **Composants Clés**:
    *   Souvent intégrée directement dans le code des classes de l'UI (fenêtres, dialogues).
    *   Modules de contrôleurs dédiés (ex: `controllers/client_controller.py`) pour découpler la logique de l'UI.
*   **Responsabilités**:
    *   Gérer l'état de l'interface utilisateur.
    *   Orchestrer les appels aux services de la Logique Métier.
    *   Transformer les données du format métier au format d'affichage et vice-versa.
    *   Gérer la navigation entre les différentes vues et dialogues.

### 2.3. Logique Métier / Services Applicatifs

*   **Description**: Cœur de l'application, contenant les règles et processus métier. Cette couche est indépendante de l'interface utilisateur.
*   **Composants Clés**:
    *   Modules dédiés par fonctionnalité (ex: `invoice_generation_logic.py`, `document_generator/`, `project_management/`, `recruitment/`, `auth/authentication.py`).
    *   Classes de service qui encapsulent des opérations métier complexes.
*   **Responsabilités**:
    *   Implémenter les règles métier (calculs, validations complexes, processus).
    *   Orchestrer les opérations impliquant plusieurs entités de données.
    *   Interagir avec la Couche d'Accès aux Données pour la persistance.
    *   Utiliser des services utilitaires (ex: envoi d'e-mails, notifications).
    *   Coordonner avec le Module de Génération de Documents.

### 2.4. Module de Génération de Documents

*   **Description**: Spécialisé dans la création de documents (PDF, DOCX, XLSX) à partir de modèles et de données.
*   **Technologies**: `python-docx`, `openpyxl`, `reportlab` (implicitement via `html_to_pdf_util.py` ou similaire), Jinja2 (pour le templating HTML).
*   **Composants Clés**:
    *   Dossier `document_generator/` (`docx_generator.py`, `html_generator.py`).
    *   `html_to_pdf_util.py` (pour la conversion HTML vers PDF).
    *   `pagedegrde.py` (pour la génération de pages de garde).
    *   Accès aux fichiers modèles stockés dans `templates/`.
*   **Responsabilités**:
    *   Charger les modèles de documents.
    *   Injecter les données dynamiques dans les modèles.
    *   Produire les fichiers de sortie dans les formats requis.
    *   Gérer la mise en page et le formatage spécifiques aux documents.

### 2.5. Couche d'Accès aux Données (DAL)

*   **Description**: Fournit une abstraction pour toutes les interactions avec la base de données. Elle isole le reste de l'application des détails spécifiques du SGBD.
*   **Technologies**: SQLAlchemy (ORM).
*   **Composants Clés**:
    *   Dossier `db/`:
        *   `connection.py`: Gère la connexion à la base de données et les sessions SQLAlchemy.
        *   `init_schema.py`: Crée le schéma de la base de données au démarrage.
        *   `db_seed.py`: Peuple la base de données avec des données initiales.
        *   Dossier `models/`: Contient les définitions des tables sous forme de classes Python (modèles SQLAlchemy).
        *   Dossier `cruds/`: Contient des modules avec des fonctions pour les opérations CRUD (Create, Read, Update, Delete) pour chaque modèle/table (ex: `clients_crud.py`, `products_crud.py`).
*   **Responsabilités**:
    *   Exécuter les opérations CRUD sur la base de données.
    *   Gérer les transactions de base de données.
    *   Traduire les objets Python en enregistrements de base de données et vice-versa.

### 2.6. Base de Données

*   **Description**: Système de persistance des données.
*   **Technologie**: SQLite (par défaut), gérée via SQLAlchemy.
*   **Composants Clés**: Fichier `client_manager_app.db` (ou nom similaire).
*   **Responsabilités**:
    *   Stocker de manière persistante toutes les données de l'application.
    *   Assurer l'intégrité référentielle (via les contraintes définies dans les modèles SQLAlchemy).
*   **Détails du schéma**: Voir [Schéma de la Base de Données](./schema_base_de_donnees.md).

### 2.7. Gestionnaire d'Authentification et Permissions

*   **Description**: Gère la connexion des utilisateurs, leurs rôles et les permissions associées.
*   **Composants Clés**:
    *   `auth/authentication.py`: Logique de vérification des identifiants, gestion des sessions utilisateur.
    *   `auth/roles.py`, `auth/permissions.py`: Définition des rôles et des permissions.
    *   `dialogs/login_dialog.py`: Interface utilisateur pour la connexion.
*   **Responsabilités**:
    *   Authentifier les utilisateurs.
    *   Charger les rôles et permissions de l'utilisateur authentifié.
    *   Fournir des mécanismes pour vérifier si un utilisateur a la permission d'effectuer une action.

### 2.8. Services Utilitaires

*   **Description**: Modules fournissant des fonctionnalités transversales et de support.
*   **Composants Clés**:
    *   `email_service.py`: Envoi d'e-mails.
    *   `notifications.py`: Gestion des notifications à l'utilisateur.
    *   `utils.py`: Fonctions utilitaires diverses.
    *   `config.py`, `app_setup.py`: Configuration et initialisation de l'application.
*   **Responsabilités**:
    *   Fournir des services communs réutilisables par d'autres couches/modules.

## 3. Serveur API Intégré (FastAPI)

*   **Description**: Un serveur API RESTful léger, basé sur FastAPI, est intégré et exécuté au sein du même processus que l'application desktop (ou peut être lancé séparément selon la configuration).
*   **Technologies**: FastAPI, Uvicorn (serveur ASGI).
*   **Composants Clés**:
    *   `api/main.py`: Point d'entrée de l'API, configuration des routeurs.
    *   Dossier `api/`: Contient les routeurs pour différents ensembles d'endpoints (ex: `api/auth.py`, `api/products.py`, `api/documents.py`).
    *   Modèles Pydantic pour la validation des données des requêtes et des réponses.
*   **Responsabilités**:
    *   Exposer certaines fonctionnalités et données de l'application via des endpoints HTTP.
    *   Gérer l'authentification et l'autorisation pour les requêtes API (souvent via des tokens).
    *   Interagir avec la Logique Métier et la Couche d'Accès aux Données pour traiter les requêtes API.
*   **Cas d'usage**: Principalement pour servir de backend à l'application mobile compagnon.

## 4. Flux de Données Typique (Exemple: Sauvegarde d'un Client)

1.  **UI**: L'utilisateur remplit le formulaire client dans un dialogue (`EditClientDialog` ou `AddNewClientDialog`) et clique sur "Sauvegarder".
2.  **Logique de Présentation**: Le dialogue récupère les données du formulaire, effectue des validations de base, puis appelle une méthode du `ClientController` (ou une fonction de la logique métier directement).
3.  **Logique Métier**: Le `ClientController` ou le service métier reçoit les données. Il peut effectuer des validations plus complexes. Ensuite, il appelle la fonction appropriée du CRUD client (ex: `clients_crud.update_client` ou `clients_crud.add_client`).
4.  **DAL (CRUD)**: La fonction CRUD interagit avec la session SQLAlchemy pour mapper les données de l'objet client à la table `clients` et exécute l'opération SQL correspondante (UPDATE ou INSERT).
5.  **Base de Données**: L'opération est effectuée sur la base de données SQLite.
6.  **Retour**: Le succès ou l'échec de l'opération est propagé en retour à travers les couches.
7.  **Logique de Présentation / UI**: L'UI est mise à jour pour refléter le changement (ex: message de succès, rafraîchissement de la liste des clients).

Cette architecture en couches vise à créer un système robuste, maintenable et évolutif. La séparation claire des responsabilités facilite les tests et les modifications futures.
