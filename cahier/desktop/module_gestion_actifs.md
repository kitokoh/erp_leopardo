# Module : Gestion des Actifs et de l'Inventaire (Desktop)

## 1. Objectif Principal

Le module de Gestion des Actifs et de l'Inventaire de ClientDocManager a pour but de permettre à l'entreprise de suivre et de gérer ses actifs (immobilisations, équipements de valeur) ainsi que potentiellement son inventaire de produits finis ou de composants (bien que la gestion de stock produit soit aussi en partie couverte par le [Module Gestion des Produits](./module_gestion_produits.md)). Ce module vise à fournir une visibilité sur les actifs détenus, leur assignation, leur état, et leur cycle de vie.

## 2. Composants Clés et Fonctionnalités

*   **Navigateur d'Inventaire/Actifs (`inventory_browser_widget.py`)**:
    *   **Affichage de la Liste des Actifs/Items d'Inventaire**: Tableau ou arborescence présentant les actifs avec des informations clés (Nom/Désignation, Numéro de Série/Identifiant Unique, Catégorie, Statut, Date d'Acquisition, Valeur, Emplacement, Personne Assignée).
    *   **Fonctionnalités de Tri et de Filtrage**: Permettre de trier la liste par différentes colonnes et de filtrer (par catégorie, statut, emplacement, personne assignée).
    *   **Recherche Rapide**: Pour trouver un actif spécifique.
    *   **Actions sur les Actifs**:
        *   Ajouter un nouvel actif.
        *   Modifier un actif existant.
        *   Supprimer ou mettre hors service un actif.
        *   Visualiser les détails complets.
        *   Gérer les assignations.
        *   Lier des médias (photos, manuels).

*   **Dialogues de Gestion des Actifs** (Noms de fichiers de dialogues spécifiques aux actifs non explicitement listés, mais supposés exister ou être intégrés dans des dialogues génériques) :
    *   **Dialogue de Création/Édition d'Actif**:
        *   Champs pour : Nom, description, catégorie d'actif, numéro de série, fabricant, modèle, date d'acquisition, coût d'acquisition, valeur actuelle.
        *   Fournisseur, informations de garantie.
        *   Statut de l'actif (En service, En maintenance, Hors service, Vendu, etc.).
        *   Emplacement physique (`db/cruds/locations_crud.py` pourrait être utilisé ici).
        *   Notes et commentaires.

*   **Gestion des Assignations d'Actifs (`db/cruds/asset_assignments_crud.py`)**:
    *   **Assignation à un Employé**: Suivi de quel employé est responsable ou utilise quel actif.
    *   **Assignation à un Emplacement/Département**: Suivi de l'emplacement physique de l'actif.
    *   Historique des assignations.
    *   Dialogue pour créer/modifier une assignation (par exemple, sélectionner un actif et un employé/emplacement, définir les dates d'assignation).

*   **Gestion des Médias liés aux Actifs (`db/cruds/asset_media_links_crud.py`)**:
    *   Possibilité d'attacher des fichiers aux actifs (photos de l'équipement, factures d'achat, manuels d'utilisation, rapports de maintenance).
    *   Interaction avec `db/cruds/media_items_crud.py` pour le stockage des informations sur les médias.

*   **Gestion des Catégories d'Actifs**:
    *   Permettre de classer les actifs en catégories (ex: Informatique, Mobilier, Véhicules, Outillage).

*   **Suivi de la Maintenance (Potentiel)**:
    *   Bien que non explicitement détaillé par les noms de fichiers CRUD, un module d'actifs pourrait inclure le suivi des maintenances préventives et correctives, des coûts de maintenance, etc.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/company_assets_crud.py`**: Fonctions CRUD pour les actifs de l'entreprise.
    *   **`db/cruds/asset_assignments_crud.py`**: CRUD pour les assignations d'actifs.
    *   **`db/cruds/asset_media_links_crud.py`**: CRUD pour les liens entre actifs et médias.
    *   **`db/models/company_assets.py`**, **`db/models/asset_assignment.py`**, **`db/models/asset_media_link.py`**: Définitions SQLAlchemy des tables.
    *   **`db/models/locations.py`** et **`db/cruds/locations_crud.py`**: Peuvent être utilisés pour définir et gérer les emplacements des actifs.

*   **Dossier `assets/`**:
    *   Ce dossier à la racine du projet semble contenir des ressources statiques (comme `world_countries.geojson`). Il est peu probable qu'il contienne la logique métier du module de gestion des actifs de l'entreprise, mais plutôt des ressources utilisées par l'application en général. Le nom "assets" ici est ambigu par rapport à "company_assets" qui réfère aux actifs de l'entreprise.

## 3. Flux de Travail Typique

### 3.1. Enregistrement d'un Nouvel Actif

1.  Un utilisateur autorisé accède au navigateur d'inventaire/actifs et clique sur "Ajouter Actif".
2.  Un dialogue de création d'actif s'ouvre.
3.  L'utilisateur remplit les détails de l'actif (nom, numéro de série, catégorie, date d'achat, coût, etc.) et peut attacher des médias (photo, facture).
4.  L'utilisateur valide. `company_assets_crud.add_asset()` est appelé.
5.  L'actif est enregistré en base de données. Les médias liés sont aussi enregistrés via `asset_media_links_crud` et `media_items_crud`.
6.  La liste dans le navigateur d'inventaire est mise à jour.

### 3.2. Assignation d'un Actif

1.  Depuis la liste des actifs ou la vue détaillée d'un actif, l'utilisateur choisit d'assigner l'actif.
2.  Un dialogue d'assignation s'ouvre, permettant de sélectionner un employé et/ou un emplacement, ainsi que les dates d'assignation.
3.  Après validation, `asset_assignments_crud.add_assignment()` est appelé.
4.  L'assignation est enregistrée, liant l'actif à l'employé/emplacement.

### 3.3. Consultation de l'Inventaire

1.  L'utilisateur ouvre le `inventory_browser_widget.py`.
2.  Il peut rechercher, trier et filtrer la liste des actifs.
3.  En sélectionnant un actif, il peut voir ses détails complets, y compris son historique d'assignations, les maintenances passées (si géré), et les médias attachés.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Employés (RH)**: Les actifs sont souvent assignés à des employés. Le module RH fournit la liste des employés.
*   **Gestion des Produits**: Si l'inventaire géré ici inclut des produits finis destinés à la vente, il y a une forte interaction. Cependant, `internal_stock_items_crud.py` (lié aux produits) et `company_assets_crud.py` semblent distincts, suggérant que "company_assets" est plus pour les immobilisations/équipements internes.
*   **Comptabilité/Finances**: La valeur des actifs, leur amortissement (non géré explicitement ici mais une extension logique), et leur coût d'acquisition sont des données importantes pour la comptabilité.
*   **Gestion des Partenaires (Fournisseurs)**: Les informations sur le fournisseur d'un actif peuvent être stockées.
*   **Base de Données**: Toutes les données sur les actifs, leurs assignations et médias sont stockées via la DAL.

## 5. Points d'Attention

*   **Distinction Actifs vs. Stock Produits**: Clarifier si ce module gère uniquement les actifs internes de l'entreprise (ordinateurs, mobilier, véhicules) ou s'il s'étend à l'inventaire des produits destinés à la vente (qui a aussi `internal_stock_items_crud.py` sous le module produit). La documentation actuelle se concentre sur les "actifs de l'entreprise".
*   **Cycle de Vie Complet**: Pour une gestion d'actifs complète, le suivi du cycle de vie (achat, mise en service, maintenance, réassignations, mise hors service, cession/vente) est important.
*   **Amortissement**: La fonctionnalité d'amortissement comptable des actifs n'est pas explicitement visible mais est une extension courante.
*   **Codes-barres/QR Codes**: Pour faciliter l'identification et l'inventaire physique, l'intégration avec des lecteurs de codes-barres/QR codes pourrait être envisagée.
*   **Audits d'Inventaire**: Fonctionnalités pour réaliser et enregistrer des audits physiques de l'inventaire des actifs.
*   **Valorisation**: Méthodes de valorisation des actifs et de l'inventaire.
