# Module : Gestion des Commandes (Desktop)

## 1. Objectif Principal

Le module de Gestion des Commandes permet de gérer le cycle de vie complet des commandes clients, depuis leur création jusqu'à leur finalisation. Il offre une interface pour enregistrer les produits commandés, générer des documents associés (comme les factures proforma), et lier chaque commande à un projet pour le suivi administratif et des tâches.

## 2. Composants Clés et Fonctionnalités

*   **Widget Principal des Commandes (`commande_management/commande_widget.py`)**:
    *   Intégré comme un onglet dans la fiche client (`client_management/client_widget.py`).
    *   **Affichage de la Liste des Commandes**: Tableau présentant les commandes existantes pour le client sélectionné. Les informations clés incluent la référence de la commande, la date, le statut, et les montants totaux.
    *   **Actions sur les Commandes**:
        *   Ajouter une nouvelle commande.
        *   Modifier une commande existante.
        *   Visualiser les détails d'une commande.
        *   Supprimer une commande (avec confirmation).
    *   **Filtrage**: Possibilité de filtrer les commandes (par exemple, par statut).

*   **Dialogue de Gestion de Commande (`commande_management/commande_dialog.py`)**:
    *   Interface modale pour la création et la modification d'une commande.
    *   **Informations Générales de la Commande**:
        *   Référence de la commande (peut être auto-générée).
        *   Date de la commande.
        *   Statut de la commande (Brouillon, Confirmée, Facturée, etc.).
        *   Description/notes.
        *   Adresses de livraison et de facturation (peuvent être reprises du client ou spécifiques à la commande).
    *   **Gestion des Lignes de Commande**:
        *   Tableau pour ajouter, modifier, ou supprimer des produits/articles à la commande.
        *   Pour chaque article : sélection du produit, description, quantité, prix unitaire HT, taux de TVA.
        *   Calcul automatique des totaux par ligne (HT et TTC).
    *   **Calcul des Totaux de la Commande**: Affichage des totaux HT et TTC globaux de la commande.
    *   **Liaison à un Projet**:
        *   Possibilité de sélectionner un projet existant du client ou de créer un nouveau projet directement depuis le dialogue de commande. Ce projet sera utilisé pour le suivi administratif et des tâches liées à la commande.
        *   Le nom/identifiant du projet peut être basé sur la référence de la commande.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/commandes_crud.py`**: Fonctions CRUD pour :
        *   `Commandes`: Créer, lire, mettre à jour, supprimer les enregistrements de commandes.
        *   `CommandeItems`: Créer, lire, mettre à jour, supprimer les lignes d'articles pour chaque commande.
    *   **Tables de Base de Données**:
        *   `Commandes`: Stocke les informations d'en-tête de la commande.
        *   `CommandeItems`: Stocke les détails de chaque produit ou service inclus dans une commande.
        *   `StatusSettings`: Contient les statuts spécifiques au type 'Commande'.

## 3. Flux de Travail Typique

### 3.1. Création d'une Nouvelle Commande

1.  **Initiation**:
    *   Après la création d'un nouveau client, l'utilisateur est invité à créer une première commande.
    *   Alternativement, depuis l'onglet "Commandes" de la fiche client, l'utilisateur clique sur "Nouvelle Commande".
2.  Le dialogue `CommandeDialog` s'ouvre.
3.  **Saisie des Informations de la Commande**:
    *   L'utilisateur remplit la référence, la date, sélectionne un statut (par défaut "Brouillon" ou équivalent).
    *   Ajoute une description si nécessaire.
4.  **Ajout des Articles**:
    *   L'utilisateur clique sur "Ajouter Article". Un mécanisme de sélection de produit (potentiellement un autre dialogue ou une recherche intégrée) permet de choisir un produit existant.
    *   La description et le prix unitaire peuvent être pré-remplis à partir du produit global, mais modifiables pour cette commande.
    *   L'utilisateur saisit la quantité et le taux de TVA applicable.
    *   Les totaux de la ligne et de la commande sont mis à jour.
    *   Répéter pour tous les articles.
5.  **Liaison au Projet**:
    *   L'utilisateur choisit un projet existant pour le client ou opte pour la création d'un nouveau projet. Si nouveau, un nom est saisi (par exemple, basé sur la référence de la commande).
6.  **Sauvegarde**:
    *   L'utilisateur valide le dialogue.
    *   La logique dans `CommandeDialog` appelle `commandes_crud.add_commande()` et `commandes_crud.add_commande_item()` pour chaque article.
    *   Si un nouveau projet doit être créé, `projects_crud.add_project()` est appelé. L'`project_id` résultant est sauvegardé dans l'enregistrement de la commande.
7.  La liste des commandes dans `CommandeWidget` est rafraîchie.

### 3.2. Modification d'une Commande

1.  Depuis `CommandeWidget`, l'utilisateur sélectionne une commande et clique sur "Modifier" (ou double-clique).
2.  `CommandeDialog` s'ouvre, pré-remplie avec les données de la commande et ses articles.
3.  L'utilisateur modifie les informations ou les articles souhaités.
4.  L'utilisateur valide. La logique appelle `commandes_crud.update_commande()` et les fonctions CRUD nécessaires pour les `CommandeItems` (ajout, modification, suppression).
5.  La liste des commandes est rafraîchie.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Clients**: Le module de commandes est principalement accessible via la fiche client. Les informations du client (adresses, etc.) peuvent pré-remplir certains champs de la commande.
*   **Gestion des Produits**: Le dialogue de commande interagit avec le catalogue de produits pour ajouter des articles aux lignes de commande.
*   **Gestion de Projet**: Chaque commande est liée à un projet. Le module de gestion de projet utilise ce projet pour le suivi des tâches et de l'avancement administratif lié à l'exécution de la commande.
*   **Gestion des Documents**: Des documents tels que les factures proforma, les confirmations de commande, ou les bons de livraison sont générés en lien avec une commande spécifique. La table `ClientDocuments` peut être étendue pour inclure un `commande_id`.
*   **Facturation**: Les factures finales sont générées sur la base des informations de la commande.
*   **Base de Données**: Stockage et récupération des données des commandes et des articles.

## 5. Points d'Attention

*   **Cohérence des Données**: Assurer la synchronisation des prix et descriptions des produits entre le catalogue global et les lignes de commande (tout en permettant des exceptions).
*   **Calculs Précis**: Les calculs des totaux HT, TTC, et des taxes doivent être exacts.
*   **Gestion des Statuts**: Le cycle de vie des statuts de commande doit être clairement défini et géré.
*   **Performance**: L'affichage des listes de commandes et le chargement des détails doivent être performants, surtout pour les clients avec de nombreuses commandes.
*   **Extensibilité**: Prévoir la possibilité d'ajouter des champs personnalisés ou des logiques spécifiques aux commandes à l'avenir.

[end of cahier/desktop/module_gestion_commandes.md]
