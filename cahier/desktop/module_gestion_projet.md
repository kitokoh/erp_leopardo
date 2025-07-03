# Module : Gestion de Projet (Desktop)

## 1. Objectif Principal

Le module de Gestion de Projet dans ClientDocManager vise à fournir des outils pour planifier, suivre, et gérer les projets de l'entreprise. Il permet d'organiser les tâches, d'allouer des ressources (si applicable), de suivre l'avancement, de gérer les documents liés aux projets, et de collaborer (potentiellement) avec les équipes impliquées. L'objectif est d'améliorer la visibilité sur les projets, de respecter les échéances et de centraliser les informations relatives à chaque projet.

## 2. Composants Clés et Fonctionnalités

*   **Tableau de Bord des Projets (`project_management/dashboard.py`)**:
    *   Vue d'ensemble de tous les projets ou des projets assignés à l'utilisateur.
    *   Affichage de listes de projets avec des informations clés (Nom du projet, Client, Statut, Date de début/fin prévue, Chef de projet, Progression).
    *   Indicateurs visuels (barres de progression, alertes pour les projets en retard).
    *   Fonctionnalités de filtrage (par statut, client, chef de projet) et de recherche.
    *   Actions : Créer un nouveau projet, ouvrir un projet existant pour voir les détails.

*   **Détail d'un Projet**:
    *   Vue spécifique pour chaque projet, affichant toutes ses informations :
        *   Description du projet, objectifs.
        *   Client associé.
        *   Chef de projet et membres de l'équipe.
        *   Dates clés (début, fin, jalons).
        *   Liste des tâches ou phases du projet.
        *   Budget et suivi des coûts (si applicable).
        *   Fichiers et documents liés au projet (`db/cruds/project_files_crud.py`).
        *   Journal d'activité du projet (`db/cruds/project_logs_crud.py`).
        *   Produits ou livrables associés (`db/cruds/client_project_products_crud.py`).

*   **Gestion des Tâches/Phases**:
    *   Possibilité de décomposer un projet en tâches, sous-tâches ou phases.
    *   Assignation des tâches à des membres de l'équipe.
    *   Définition des dates de début/fin pour chaque tâche.
    *   Suivi du statut de chaque tâche (À faire, En cours, Terminé, Bloqué).
    *   Dépendances entre les tâches (si géré).

*   **Gestion des Jalons (`db/cruds/milestones_crud.py`, `dialogs/add_edit_milestone_dialog.py`)**:
    *   Définition des étapes importantes (jalons) d'un projet avec des dates cibles.
    *   Suivi de l'atteinte des jalons.

*   **Gestion des Statuts de Projet (`dialogs/add_edit_status_dialog.py`, `dialogs/status_management_dialog.py`)**:
    *   Permettre de définir et de gérer différents statuts pour les projets et potentiellement pour les tâches (ex: Planifié, En cours, En attente, Terminé, Annulé).

*   **Gestion des Documents de Projet**:
    *   Téléchargement et organisation des fichiers pertinents pour chaque projet (cahiers des charges, plans, rapports, contrats, etc.).
    *   Liaison avec `db/cruds/project_files_crud.py`.
    *   **Pages de Garde pour Projets (`project_management/dialogs/cover_page_editor_dialog.py`)**: Outil pour créer ou personnaliser des pages de garde pour les documents de projet.
    *   Interaction avec `db/cruds/cover_pages_crud.py` et `db/cruds/cover_page_templates_crud.py`.

*   **Gestion des Ordres de Production (si applicable, `project_management/dialogs/add_production_order_dialog.py`, etc.)**:
    *   Si les projets impliquent une production physique, ce sous-module permet de gérer les ordres de production, les étapes de production, et leur suivi.
    *   Interaction avec `db/cruds/production_orders_crud.py`, `db/cruds/production_steps_crud.py`.

*   **Notifications de Projet (`project_management/notifications.py`)**:
    *   Système de notifications pour les événements importants du projet (nouvelle tâche assignée, jalon approchant, tâche en retard, etc.).
    *   Intégration avec le système de notification global de l'application.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/projects_crud.py`**: Fonctions CRUD pour les projets.
    *   **`db/cruds/tasks_crud.py`** (nom supposé, ou logique intégrée) : CRUD pour les tâches.
    *   Autres CRUDs spécifiques mentionnés ci-dessus (`milestones_crud`, `project_files_crud`, etc.).
    *   **`db/models/projects.py`**, **`db/models/tasks.py`** (supposé), **`db/models/milestones.py`**, etc. : Définitions SQLAlchemy des tables.

## 3. Flux de Travail Typique

### 3.1. Création d'un Nouveau Projet

1.  Depuis le tableau de bord des projets, l'utilisateur (généralement un chef de projet ou un administrateur) clique sur "Créer un Projet".
2.  Un dialogue de création de projet s'ouvre.
3.  L'utilisateur saisit les informations de base du projet (nom, description, client associé, dates de début/fin prévues, chef de projet).
4.  Le projet est enregistré en base de données via `projects_crud.add_project()`.
5.  L'utilisateur peut ensuite accéder à la vue détaillée du projet pour ajouter des tâches, des jalons, des documents, et assigner des membres d'équipe.

### 3.2. Suivi de l'Avancement d'un Projet

1.  Le chef de projet ou les membres de l'équipe consultent la vue détaillée du projet.
2.  Ils mettent à jour le statut des tâches (ex: "En cours" -> "Terminé").
3.  Ils enregistrent le temps passé sur les tâches (si cette fonctionnalité existe).
4.  Ils marquent les jalons comme atteints.
5.  Le tableau de bord des projets et la vue détaillée reflètent la progression (pourcentage d'achèvement, statut général).

### 3.3. Gestion des Documents d'un Projet

1.  Depuis la vue détaillée d'un projet, un utilisateur avec les droits appropriés télécharge un nouveau document (ex: un compte-rendu de réunion).
2.  Le fichier est stocké (sur le serveur ou un emplacement défini) et une référence est enregistrée en base de données via `project_files_crud.add_file()`, liant le document au projet.
3.  Les membres de l'équipe peuvent consulter les documents liés au projet.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Clients**: Les projets sont généralement associés à un client. Les informations du client sont affichées dans le contexte du projet.
*   **Gestion des Documents**: De nombreux documents (contrats, spécifications, rapports) sont générés ou stockés dans le cadre d'un projet. Le module de gestion de projet offre un contexte pour organiser ces documents.
*   **Gestion des Produits**: Si le projet concerne la livraison de produits spécifiques, ceux-ci peuvent être liés au projet.
*   **Authentification et Gestion des Utilisateurs**: Les chefs de projet et les membres de l'équipe sont des utilisateurs de l'application. Leurs rôles et permissions peuvent déterminer leur accès et leurs actions possibles sur les projets.
*   **Calendrier/Agenda**: Les dates clés des projets (début, fin, jalons, échéances des tâches) peuvent être intégrées au module calendrier.
*   **Notifications**: Le système de notification de l'application est utilisé pour les alertes et mises à jour relatives aux projets.
*   **Facturation et Paiements**: L'achèvement de jalons ou la finalisation de projets peuvent déclencher des processus de facturation.
*   **Base de Données**: Toutes les données relatives aux projets (détails, tâches, documents, etc.) sont stockées et gérées via la couche d'accès aux données.

## 5. Points d'Attention

*   **Complexité vs Simplicité**: Le module doit trouver un équilibre entre offrir suffisamment de fonctionnalités pour une gestion de projet efficace et rester simple d'utilisation.
*   **Collaboration**: Si plusieurs utilisateurs collaborent sur un projet, la gestion des accès concurrents et la communication (commentaires, notifications) sont importantes.
*   **Personnalisation**: Les entreprises ont souvent des méthodologies de gestion de projet différentes. La flexibilité (champs personnalisés, types de tâches, workflows de statut) peut être un avantage.
*   **Reporting de Projet**: Des fonctionnalités de reporting sur l'état des projets, l'utilisation des ressources, le respect des délais sont précieuses.
*   **Intégration avec d'autres outils**: Pour les entreprises utilisant déjà des outils de gestion de projet spécialisés, des possibilités d'intégration ou d'export de données pourraient être envisagées.
