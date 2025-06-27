# Module : API Backend Intégrée (FastAPI - Desktop)

## 1. Objectif Principal

L'application ClientDocManager intègre un serveur API backend développé avec FastAPI. L'objectif principal de cette API est d'exposer certaines fonctionnalités et données de l'application de manière programmatique via des points de terminaison (endpoints) HTTP. Cela permet potentiellement :

*   L'interaction avec des clients externes, comme l'application mobile ClientDocManager.
*   Des intégrations avec d'autres systèmes tiers.
*   L'automatisation de certaines tâches via des scripts ou d'autres applications.
*   Des fonctionnalités internes où l'application desktop elle-même pourrait consommer sa propre API pour certaines opérations (moins courant pour une architecture client lourd monolithique, mais possible).

## 2. Composants Clés et Architecture

*   **Serveur API (FastAPI)**:
    *   **Technologie**: FastAPI, un framework Python moderne pour construire des APIs.
    *   **Serveur ASGI**: Uvicorn est utilisé pour exécuter l'application FastAPI (comme vu dans `main.py` qui lance `uvicorn api.main:app`).
    *   **Démarrage**: Le serveur API est démarré en tant que sous-processus par l'application desktop principale (`main.py`) lors de son lancement (bien que cela puisse être conditionnel ou configurable).

*   **Point d'Entrée de l'API (`api/main.py`)**:
    *   Initialise l'application FastAPI.
    *   Inclut les routeurs des différents modules de l'API.
    *   Peut définir des middlewares (pour logging, CORS, authentification API, etc.).
    *   Définit potentiellement des endpoints globaux (ex: `/health` pour vérifier l'état de l'API).

*   **Routeurs Modulaires (dans `api/`)**:
    *   L'API est organisée en plusieurs fichiers routeurs, chacun regroupant les endpoints pour une ressource ou une fonctionnalité spécifique. Exemples basés sur la structure des fichiers :
        *   **`api/auth.py`**: Endpoints pour l'authentification des utilisateurs de l'API (génération de tokens, vérification).
        *   **`api/assets.py`**: Endpoints pour la gestion des actifs.
        *   **`api/company_expenses_api.py`**: Endpoints pour les dépenses de l'entreprise.
        *   **`api/company_factures_api.py`**: Endpoints pour les factures fournisseurs.
        *   **`api/documents.py`**: Endpoints pour la gestion des documents.
        *   **`api/employee_documents.py`**: Endpoints pour les documents des employés.
        *   **`api/employees.py`**: Endpoints pour la gestion des employés.
        *   **`api/hr_reports.py`**: Endpoints pour les rapports RH.
        *   **`api/leave.py`**: Endpoints pour la gestion des congés.
        *   **`api/payments.py`**: Endpoints pour les paiements.
        *   **`api/performance.py`**: Endpoints pour la gestion de la performance.
        *   **`api/products.py`**: Endpoints pour la gestion des produits.
        *   **`api/proformas.py`**: Endpoints pour les factures proforma.
        *   **`api/recruitment.py`**: Endpoints pour le module de recrutement.
        *   **`api/reports.py`**: Endpoints pour les rapports généraux.
        *   **`api/templates.py`**: Endpoints pour la gestion des modèles de documents.
    *   Chaque routeur utilise des décorateurs FastAPI (comme `@router.get`, `@router.post`) pour définir les opérations HTTP, les chemins, et la validation des données d'entrée/sortie à l'aide de modèles Pydantic.

*   **Modèles de Données Pydantic (`api/models.py` ou définis localement dans chaque routeur)**:
    *   Utilisés par FastAPI pour la validation des données des requêtes et la sérialisation des réponses.
    *   Assurent que les données échangées via l'API respectent un schéma défini.

*   **Dépendances FastAPI (`api/dependencies.py`)**:
    *   Définit des dépendances réutilisables pour les endpoints, par exemple, pour :
        *   Obtenir l'utilisateur actuellement authentifié à partir d'un token.
        *   Gérer les connexions à la base de données pour un scope de requête.
        *   Vérifier les permissions d'accès à l'API.

*   **Interaction avec la Logique Métier et la DAL**:
    *   Les fonctions définies dans les endpoints de l'API appellent typiquement la logique métier de l'application (services) ou interagissent directement avec la couche d'accès aux données (CRUDs) pour effectuer les opérations demandées.
    *   Elles partagent la même base de code et la même base de données que l'application desktop.

*   **Authentification et Sécurité de l'API**:
    *   L'API doit implémenter un mécanisme d'authentification pour protéger ses endpoints (par exemple, tokens JWT OAuth2 Bearer, clés API).
    *   `api/auth.py` semble jouer un rôle central dans ce processus.
    *   La communication devrait se faire via HTTPS en production.

## 3. Flux de Travail Typique (Exemple : Récupération de la liste des produits via l'API)

1.  Un client API (ex: l'application mobile, un script) envoie une requête `GET` à l'endpoint `/api/products/` (chemin exact à vérifier dans `api/products.py`).
2.  La requête peut inclure un token d'authentification dans les en-têtes.
3.  Le serveur FastAPI reçoit la requête.
4.  Un middleware ou une dépendance vérifie le token d'authentification (via `api/auth.py` et `api/dependencies.py`).
5.  Si l'authentification réussit, la fonction associée à l'endpoint dans `api/products.py` est exécutée.
6.  Cette fonction interagit avec `db/cruds/products_crud.py` pour récupérer la liste des produits de la base de données.
7.  Les données récupérées sont formatées (probablement en utilisant des modèles Pydantic) et retournées en tant que réponse JSON.
8.  Le client API reçoit la réponse JSON avec la liste des produits.

## 4. Documentation de l'API (Swagger/OpenAPI)

*   FastAPI génère automatiquement une documentation interactive de l'API (basée sur la spécification OpenAPI) qui est généralement accessible via les chemins `/docs` (Swagger UI) et `/redoc` (ReDoc) de l'URL de base de l'API.
*   Cette documentation détaille tous les endpoints, leurs paramètres, les schémas de données des requêtes et des réponses, et permet de tester les endpoints directement depuis le navigateur.

## 5. Interactions avec d'Autres Modules de l'Application Desktop

*   **Logique Métier et Services**: L'API est une "façade" sur la logique métier existante. Elle ne réimplémente pas la logique mais l'expose.
*   **Couche d'Accès aux Données (DAL)**: L'API utilise la même DAL (CRUDs, modèles SQLAlchemy) que le reste de l'application desktop pour interagir avec la base de données.
*   **Authentification**: Le mécanisme d'authentification de l'API (`api/auth.py`) peut être lié ou distinct de celui de l'interface utilisateur desktop. Il est crucial pour sécuriser l'accès.
*   **Base de Données**: L'API lit et écrit dans la même base de données que l'application desktop.

## 6. Points d'Attention

*   **Sécurité**: L'authentification, l'autorisation (vérification des permissions pour chaque endpoint), la validation des entrées, et la protection contre les vulnérabilités web courantes (injection SQL, XSS - bien que moins directes avec FastAPI) sont cruciales.
*   **Performance**: Les endpoints de l'API doivent être performants pour ne pas dégrader l'expérience des clients API ni surcharger le serveur.
*   **Gestion des Erreurs**: L'API doit retourner des codes de statut HTTP appropriés et des messages d'erreur clairs et standardisés.
*   **Versioning de l'API**: Pour les évolutions futures, une stratégie de versioning de l'API (ex: `/api/v1/...`, `/api/v2/...`) peut être nécessaire pour maintenir la compatibilité avec les anciens clients.
*   **Concurrence**: Étant donné que l'API s'exécute dans le même environnement que l'application desktop (partageant potentiellement des ressources comme la base de données), la gestion de la concurrence et des transactions doit être soignée.
*   **Dépendance au Cycle de Vie de l'Application Desktop**: Puisque le serveur API est lancé par `main.py`, il est lié au cycle de vie de l'application desktop. Si l'application desktop est fermée, l'API cesse de fonctionner. Pour une API destinée à une haute disponibilité, un déploiement séparé serait plus approprié.
*   **Documentation Externe**: Bien que FastAPI génère une documentation OpenAPI, une documentation conceptuelle externe (comme ce document) reste utile pour expliquer le rôle de l'API dans l'écosystème global.

## 7. Principaux Routeurs et Endpoints Attendus

Ce qui suit est une liste des principaux fichiers de routeurs identifiés dans le dossier `api/` et une suggestion des types d'endpoints qu'ils pourraient exposer. Pour une liste exhaustive et détaillée des endpoints, des paramètres et des schémas de réponse, il faut se référer à la documentation OpenAPI auto-générée par FastAPI (généralement accessible via `/docs` sur l'URL de base de l'API).

*   **`api/auth.py`**: Authentification
    *   `POST /token`: Obtention d'un token d'accès (OAuth2 Password Flow).
    *   `GET /users/me`: Récupération des informations de l'utilisateur courant (authentifié).

*   **`api/assets.py`**: Gestion des Actifs de l'Entreprise
    *   `GET /assets/`: Lister tous les actifs.
    *   `POST /assets/`: Créer un nouvel actif.
    *   `GET /assets/{asset_id}`: Obtenir les détails d'un actif spécifique.
    *   `PUT /assets/{asset_id}`: Mettre à jour un actif.
    *   `DELETE /assets/{asset_id}`: Supprimer un actif.
    *   Endpoints pour les assignations et les médias liés aux actifs.

*   **`api/company_expenses_api.py`**: Dépenses de l'Entreprise
    *   `GET /company-expenses/`: Lister toutes les dépenses.
    *   `POST /company-expenses/`: Enregistrer une nouvelle dépense.

*   **`api/company_factures_api.py`**: Factures Fournisseurs
    *   `GET /supplier-invoices/`: Lister toutes les factures fournisseurs.
    *   `POST /supplier-invoices/`: Enregistrer une nouvelle facture fournisseur.

*   **`api/documents.py`**: Gestion des Documents (génériques ou types non spécifiques)
    *   `GET /documents/`: Lister les documents.
    *   `POST /documents/`: Créer/uploader un nouveau document.
    *   Endpoints pour la recherche, le téléchargement, la mise à jour des métadonnées.

*   **`api/employee_documents.py`**: Documents des Employés
    *   `GET /employees/{employee_id}/documents/`: Lister les documents d'un employé.
    *   `POST /employees/{employee_id}/documents/`: Ajouter un document à un employé.

*   **`api/employees.py`**: Gestion des Employés
    *   `GET /employees/`: Lister tous les employés.
    *   `POST /employees/`: Créer un nouvel employé.
    *   `GET /employees/{employee_id}`: Détails d'un employé.
    *   `PUT /employees/{employee_id}`: Mettre à jour un employé.

*   **`api/hr_reports.py`**: Rapports RH
    *   `GET /hr-reports/{report_type}`: Générer des rapports RH spécifiques.

*   **`api/leave.py`**: Gestion des Congés
    *   `GET /leave-requests/`: Lister les demandes de congé.
    *   `POST /leave-requests/`: Soumettre une demande de congé.
    *   `PUT /leave-requests/{request_id}/status`: Approuver/rejeter une demande.

*   **`api/payments.py`**: Paiements (clients)
    *   `GET /payments/`: Lister les paiements.
    *   `POST /payments/`: Enregistrer un nouveau paiement pour une facture.

*   **`api/performance.py`**: Suivi de Performance (employés)
    *   `GET /performance-reviews/`: Lister les revues de performance.
    *   `POST /performance-reviews/`: Créer une nouvelle revue.

*   **`api/products.py`**: Gestion des Produits
    *   `GET /products/`: Lister tous les produits.
    *   `POST /products/`: Créer un nouveau produit.
    *   `GET /products/{product_id}`: Détails d'un produit.
    *   `PUT /products/{product_id}`: Mettre à jour un produit.

*   **`api/proformas.py`**: Factures Proforma
    *   `GET /proformas/`: Lister les factures proforma.
    *   `POST /proformas/`: Créer une nouvelle facture proforma.
    *   `GET /proformas/{proforma_id}`: Détails d'une proforma.

*   **`api/recruitment.py`**: Recrutement
    *   `GET /job-openings/`: Lister les offres d'emploi.
    *   `POST /job-openings/`: Créer une offre.
    *   `GET /candidates/`: Lister les candidats.
    *   `POST /candidates/`: Ajouter un candidat.
    *   Endpoints pour les entretiens, le suivi des candidatures.

*   **`api/reports.py`**: Rapports Généraux
    *   `GET /reports/{report_name}`: Générer des rapports spécifiques (ventes, financiers, etc.).
    *   Paramètres pour les dates, filtres.

*   **`api/templates.py`**: Gestion des Modèles de Documents
    *   `GET /templates/`: Lister les modèles disponibles.
    *   `GET /templates/{template_id}/content`: Obtenir le contenu d'un modèle (utilisé par l'app mobile).
    *   `POST /templates/`: Uploader un nouveau modèle.

*(Note : Les chemins exacts des endpoints, les méthodes HTTP et les paramètres peuvent varier. Cette liste est une supposition éclairée basée sur les noms des fichiers routeurs et les fonctionnalités typiques.)*

