# Architecture Générale - Application Desktop ClientDocManager

## 1. Introduction

Ce document décrit l'architecture générale de l'application desktop ClientDocManager. L'application est développée en Python avec le framework PyQt5 pour l'interface utilisateur et s'appuie sur une base de données (probablement SQLite par défaut) pour la persistance des données. Elle intègre également un serveur API FastAPI, qui pourrait être utilisé pour des fonctionnalités internes ou pour une communication avec des clients externes (comme l'application mobile).

## 2. Vue d'Ensemble de l'Architecture

L'application ClientDocManager est une application client lourd (desktop) qui peut être décomposée en plusieurs couches et composants principaux :

```mermaid
graph TD
    A[Utilisateur] --> B[Interface Utilisateur (PyQt5)];

    subgraph ClientDocManager Application
        B --> C{Logique de Présentation / Contrôleurs};
        C --> D[Logique Métier / Services];
        D --> E[Couche d'Accès aux Données (CRUDs)];
        E --> F[Base de Données (SQLite/autre)];
        D --> G[Générateur de Documents];
        C --> H[Gestionnaire d'Authentification];
        H --> E;
        D --> I[Services Externes (Email, Notifications)];

        J[Serveur API (FastAPI)];
        J --> D;
        J --> E;

        K[Application Mobile (Client Externe)];
        K -.-> J;
    end

    style B fill:#cde,stroke:#333,stroke-width:2px
    style F fill:#dbf,stroke:#333,stroke-width:2px
    style J fill:#dec,stroke:#333,stroke-width:2px
```

## 3. Composants Principaux

*   **Interface Utilisateur (UI)**:
    *   **Description**: Responsable de la présentation des informations à l'utilisateur et de la capture de ses actions. Elle est construite avec PyQt5.
    *   **Composants Clés**: `main_window.py` (Fenêtre principale `DocumentManager`), nombreux dialogues dans `dialogs/`, widgets personnalisés (`client_widget.py`, etc.), `settings_page.py`, `home_page_widget.py`.
    *   **Interactions**: Interagit avec la Logique de Présentation pour afficher les données et notifier les actions utilisateur.

*   **Logique de Présentation / Contrôleurs**:
    *   **Description**: Sert de pont entre l'UI et la Logique Métier. Elle traite les événements de l'UI, récupère les données nécessaires via la logique métier, et prépare les données pour l'affichage.
    *   **Composants Clés**: Souvent intégrée dans les classes de l'UI (dialogues, widgets principaux), ou dans des modules dédiés comme `controllers/client_controller.py`.
    *   **Interactions**: Reçoit les événements de l'UI, appelle les services de la Logique Métier, et met à jour l'UI.

*   **Logique Métier / Services**:
    *   **Description**: Contient les règles métier de l'application. Elle orchestre les opérations, traite les données et prend des décisions basées sur la logique de l'application.
    *   **Composants Clés**: Fonctions et classes dans divers modules comme `document_generator/`, `invoice_generation_logic.py`, `email_service.py`, `auth/authentication.py`, `project_management/`, `recruitment/`, etc.
    *   **Interactions**: Est appelée par la Logique de Présentation. Interagit avec la Couche d'Accès aux Données pour la persistance, et peut utiliser des services externes.

*   **Couche d'Accès aux Données (Data Access Layer - DAL)**:
    *   **Description**: Responsable de toutes les interactions avec la base de données. Elle abstrait les opérations CRUD (Create, Read, Update, Delete).
    *   **Composants Clés**: Le module `db/` avec `db/connection.py`, `db/init_schema.py`, et tous les modules CRUD dans `db/cruds/` (ex: `clients_crud.py`, `products_crud.py`, `users_crud.py`). Les modèles de données sont définis dans `db/models/`.
    *   **Interactions**: Fournit des méthodes à la Logique Métier pour manipuler les données sans exposer les détails de la base de données.

*   **Base de Données**:
    *   **Description**: Système de persistance des données de l'application.
    *   **Technologie**: SQLite est souvent utilisé par défaut pour les applications desktop Python, mais la structure avec SQLAlchemy (visible dans `db/models/`) permet une portabilité vers d'autres SGBD.
    *   **Interactions**: Accédée exclusivement via la Couche d'Accès aux Données.

*   **Générateur de Documents**:
    *   **Description**: Responsable de la création de documents (PDF, DOCX, etc.) à partir de modèles et de données.
    *   **Composants Clés**: `document_generator/` (avec `docx_generator.py`, `html_generator.py`), `html_to_pdf_util.py`.
    *   **Interactions**: Utilisé par la Logique Métier.

*   **Gestionnaire d'Authentification**:
    *   **Description**: Gère l'authentification des utilisateurs, les rôles et les permissions.
    *   **Composants Clés**: `auth/authentication.py`, `auth/roles.py`, `auth/permissions.py`, `dialogs/login_dialog.py`.
    *   **Interactions**: Interagit avec l'UI pour la connexion, et avec la DAL pour vérifier les informations d'identification et récupérer les rôles/permissions.

*   **Serveur API (FastAPI)**:
    *   **Description**: Un serveur API intégré (lancé par `main.py`) basé sur FastAPI. Il expose certaines fonctionnalités de l'application via des endpoints HTTP.
    *   **Composants Clés**: `api/main.py` (point d'entrée de l'API), et les différents routeurs dans `api/` (ex: `api/auth.py`, `api/products.py`).
    *   **Interactions**: Peut être consommé par des clients externes (comme l'application mobile) ou potentiellement par des parties de l'application desktop elle-même. Il interagit avec la Logique Métier et la DAL.

*   **Services Externes / Utilitaires**:
    *   **Description**: Modules fournissant des fonctionnalités spécifiques comme l'envoi d'e-mails, la gestion des notifications, etc.
    *   **Composants Clés**: `email_service.py`, `notifications.py`, `utils.py`.

## 4. Technologies Clés

*   **Langage**: Python 3.x.
*   **Interface Utilisateur**: PyQt5.
*   **Base de Données**: SQLAlchemy (ORM) avec une base de données sous-jacente (probablement SQLite par défaut).
*   **Serveur API**: FastAPI (avec Uvicorn comme serveur ASGI).
*   **Génération de Documents**: python-docx, Jinja2 (pour le templating HTML), et un outil de conversion HTML vers PDF (non spécifié directement, mais `html_to_pdf_util.py` suggère son utilisation).
*   **Gestion des Dépendances**: `requirements.txt`.
*   **Packaging**: Potentiellement PyInstaller (présence d'un `main.spec`).

## 5. Flux de Données et Interactions Notables

*   **Démarrage de l'Application (`main.py`)**:
    1.  Initialisation (logging, base de données via `db.initialize_database()`, seeding via `db_seed.run_seed()`).
    2.  Démarrage optionnel du serveur API FastAPI.
    3.  Gestion de la configuration initiale et de la création d'entreprise par défaut.
    4.  Processus d'authentification (via `LoginDialog`).
    5.  Si authentification réussie, affichage de la fenêtre principale (`DocumentManager`).

*   **Interaction Utilisateur (Exemple : Ajout d'un client)**:
    1.  L'utilisateur clique sur un bouton "Ajouter Client" dans l'UI.
    2.  Un dialogue (`AddNewClientDialog`) s'ouvre.
    3.  L'utilisateur remplit les informations et valide.
    4.  La logique du dialogue (ou un contrôleur associé) récupère les données.
    5.  Elle appelle un service de la Logique Métier pour créer le client.
    6.  Le service Logique Métier valide les données et appelle la méthode appropriée du CRUD client (`db/cruds/clients_crud.py`).
    7.  Le CRUD interagit avec la base de données pour insérer le nouveau client.
    8.  Un retour (succès/échec) est propagé vers l'UI, qui affiche une notification et met à jour la liste des clients.

*   **Génération de Document**:
    1.  L'utilisateur initie une action de génération de document depuis l'UI.
    2.  La Logique de Présentation collecte les données nécessaires (ID client, produits, etc.).
    3.  Elle appelle le service de Génération de Documents.
    4.  Le service récupère le contexte complet (données client, entreprise, produits) via la DAL.
    5.  Il charge le modèle de document approprié.
    6.  Il effectue le rendu du modèle avec les données (par exemple, HTML avec Jinja2).
    7.  Si c'est un PDF, le HTML est converti en PDF (potentiellement via l'API interne ou un utilitaire).
    8.  Le document généré est sauvegardé et/ou présenté à l'utilisateur.

## 6. Considérations d'Architecture

*   **Modularité**: Le projet est structuré en de nombreux dossiers et sous-dossiers, ce qui suggère une tentative de modularité. Chaque fonctionnalité majeure (clients, produits, facturation, recrutement, etc.) semble avoir ses propres composants UI, logique et parfois CRUD.
*   **Couplage UI-Logique**: Dans certains cas (notamment les dialogues), la logique de présentation et la logique métier peuvent être étroitement liées au code de l'interface utilisateur. L'utilisation de contrôleurs dédiés (`client_controller.py`) vise à découpler cela.
*   **API Intégrée**: La présence d'une API FastAPI intégrée est un point notable. Elle permet à l'application de servir de backend pour d'autres services (comme l'application mobile) ou d'exposer ses fonctionnalités de manière programmatique.
*   **Gestion de la Configuration**: `config.py` et `app_setup.py` jouent un rôle important dans la configuration et l'initialisation de l'application.

Cette architecture permet une application riche en fonctionnalités, mais sa maintenance et son évolution peuvent nécessiter une attention particulière pour maintenir une séparation claire des préoccupations entre les différentes couches et modules.
