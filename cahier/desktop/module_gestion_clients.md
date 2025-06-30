# Module : Gestion des Clients (Desktop)

## 1. Objectif Principal

Le module de Gestion des Clients est une composante essentielle de ClientDocManager. Son objectif est de fournir une interface centralisée et efficace pour enregistrer, consulter, mettre à jour et gérer toutes les informations relatives aux clients de l'entreprise. Une bonne gestion des clients est cruciale pour les activités commerciales, la génération de documents et le suivi des interactions.

## 2. Composants Clés et Fonctionnalités

*   **Widget Principal des Clients (`client_widget.py`)**:
    *   **Affichage de la Liste des Clients**: Tableau ou liste présentant les clients existants avec des informations clés (Nom, Entreprise, Contact, Statut, etc.).
    *   **Fonctionnalités de Tri et de Filtrage**: Permettre de trier la liste par différentes colonnes et de filtrer les clients selon divers critères (par exemple, par statut, par commercial assigné, par date de création).
    *   **Recherche Rapide**: Champ de recherche pour trouver rapidement un client par son nom, son entreprise ou d'autres identifiants.
    *   **Actions sur les Clients**: Boutons ou menus contextuels pour :
        *   Ajouter un nouveau client.
        *   Modifier un client existant.
        *   Supprimer un client (avec confirmation, et potentiellement archivage au lieu de suppression physique).
        *   Visualiser les détails complets d'un client.
        *   Accéder aux documents liés à un client.
        *   Initier la création de documents pour un client (ex: nouvelle proforma).
    *   **Pagination**: Si le nombre de clients est important, un système de pagination pour naviguer dans la liste.

*   **Contrôleur Client (`controllers/client_controller.py`)**:
    *   **Logique de Présentation**: Sert d'intermédiaire entre `client_widget.py` (et les dialogues associés) et les services de logique métier ou la couche d'accès aux données.
    *   **Validation des Données**: Peut inclure la validation des informations saisies par l'utilisateur avant de les envoyer à la base de données.
    *   **Coordination des Actions**: Gère le flux des opérations (par exemple, ce qui se passe après qu'un client est sauvegardé).

*   **Dialogues de Gestion des Clients**:
    *   **`dialogs/add_new_client_dialog.py`**: Interface modale pour la création d'un nouveau client. Comprend des champs pour toutes les informations pertinentes :
        *   Informations de base (nom, prénom, société, SIRET/TVA).
        *   Coordonnées (adresses multiples, e-mails, numéros de téléphone).
        *   Contacts multiples au sein de l'entreprise cliente.
        *   Statut du client, commercial assigné.
        *   Informations bancaires, conditions de paiement.
        *   Champs personnalisés si l'application le permet.
    *   **`dialogs/edit_client_dialog.py`**: Similaire à `AddNewClientDialog`, mais pré-remplie avec les informations d'un client existant pour modification.
    *   **`dialogs/assign_personnel_dialog.py`**: Pour assigner des membres du personnel (commerciaux, chargés de compte) à un client.
    *   **`dialogs/assign_document_dialog.py`**, **`dialogs/client_document_note_dialog.py`**: Pour lier des documents existants à un client ou ajouter des notes spécifiques à ces documents dans le contexte du client.
    *   **`dialogs/assign_freight_forwarder_dialog.py`**, **`dialogs/assign_money_transfer_agent_dialog.py`**, **`dialogs/assign_transporter_dialog.py`**: Dialogues pour lier des partenaires logistiques ou financiers spécifiques à un client, ce qui est particulièrement utile pour les entreprises de commerce international.

*   **Informations Détaillées du Client**:
    *   Une vue ou un onglet dédié affichant toutes les informations d'un client sélectionné, y compris :
        *   Historique des interactions/commandes.
        *   Liste des documents associés (devis, factures, contrats).
        *   Contacts clés.
        *   Notes et commentaires.
        *   Projets liés.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/clients_crud.py`**: Fonctions CRUD pour créer, lire, mettre à jour, et supprimer/archiver les clients dans la base de données.
    *   **`db/cruds/contacts_crud.py`**: CRUD pour les contacts associés aux clients.
    *   **`db/cruds/client_documents_crud.py`**, **`db/cruds/client_assigned_personnel_crud.py`**, etc. : CRUDs pour les entités liées aux clients.
    *   **`db/models/clients.py`** (et autres modèles liés) : Définition SQLAlchemy de la table des clients et des tables associées.

*   **Archivage des Clients (`archived_clients/`)**:
    *   Fonctionnalité pour archiver des clients inactifs au lieu de les supprimer définitivement, conservant ainsi l'historique. Le dossier `archived_clients/` pourrait contenir la logique ou des utilitaires pour cela, ou simplement être un placeholder pour une future fonctionnalité.

## 3. Flux de Travail Typique

### 3.1. Ajout d'un Nouveau Client

1.  L'utilisateur clique sur le bouton "Ajouter Client" dans le `client_widget.py`.
2.  `AddNewClientDialog` s'ouvre.
3.  L'utilisateur remplit les champs d'information du client.
4.  L'utilisateur valide le dialogue.
5.  La logique dans `AddNewClientDialog` (ou déléguée au `client_controller.py`) récupère les données saisies.
6.  Les données sont validées.
7.  `clients_crud.add_client()` est appelé pour insérer le nouveau client dans la base de données. Les contacts associés, adresses, etc., sont également créés via leurs CRUDs respectifs.
8.  L'utilisateur est ensuite invité à créer une **Commande** pour ce nouveau client.
    *   Si l'utilisateur accepte, le dialogue de création de commande s'ouvre (`commande_management/commande_dialog.py`).
    *   La création de la commande peut entraîner la création automatique ou la liaison à un **Projet** (pour le suivi administratif et des tâches).
9.  Le `client_widget.py` est notifié et rafraîchit sa liste pour afficher le nouveau client. Un nouvel onglet "Commandes" est disponible dans la fiche client pour gérer les commandes associées.

### 3.2. Consultation et Modification d'un Client

1.  L'utilisateur sélectionne un client dans la liste du `client_widget.py`.
2.  Les détails du client peuvent s'afficher dans un panneau de prévisualisation ou l'utilisateur clique sur "Modifier".
3.  `EditClientDialog` s'ouvre, pré-rempli avec les données du client.
4.  L'utilisateur modifie les informations souhaitées et valide.
5.  La logique du dialogue (ou du contrôleur) appelle `clients_crud.update_client()` (et les CRUDs des entités liées si nécessaire).
6.  La base de données est mise à jour.
7.  Le `client_widget.py` et toute autre vue affichant les informations du client sont rafraîchis.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Documents**: Essentiel pour lier les documents (devis, factures, contrats) aux clients et potentiellement à leurs commandes spécifiques.
*   **Gestion des Commandes**: Le module de gestion des clients est le point d'entrée pour créer et visualiser les commandes associées à un client. Chaque client peut avoir plusieurs commandes.
*   **Facturation et Paiements**: Les factures sont émises pour des clients spécifiques, souvent en lien avec une commande.
*   **Gestion de Projet**: Chaque commande est associée à un projet pour le suivi administratif et des tâches. Le module de gestion de projet interagit donc étroitement.
*   **Gestion des Contacts**: Les contacts individuels sont généralement associés à des entreprises clientes.
*   **Rapports et Statistiques**: Les données clients et commandes sont une source majeure pour les rapports de vente, d'activité commerciale, etc.
*   **Authentification et Gestion des Utilisateurs**: Le commercial ou l'agent assigné à un client est un utilisateur de l'application. Des permissions peuvent exister pour limiter qui peut voir ou modifier quels clients.
*   **Base de Données**: Toutes les informations des clients sont stockées et gérées via la couche d'accès aux données.

## 5. Points d'Attention

*   **Qualité des Données**: L'exactitude et l'exhaustivité des informations clients sont primordiales. Des mécanismes de validation et de dédoublonnage (si possible) sont importants.
*   **Historisation des Modifications**: Pour certaines informations sensibles (ex: conditions de paiement), un historique des modifications pourrait être utile.
*   **Protection des Données (RGPD/Confidentialité)**: Si des données personnelles sont stockées, s'assurer de la conformité avec les réglementations en vigueur.
*   **Performance**: L'affichage et la recherche dans une grande base de clients doivent rester performants.
*   **Champs Personnalisables**: Selon les besoins de l'entreprise, la possibilité d'ajouter des champs personnalisés aux fiches clients peut être un atout majeur.
