# Module : Gestion des Contacts (Desktop)

## 1. Objectif Principal

Le module de Gestion des Contacts dans ClientDocManager a pour objectif de fournir un répertoire centralisé pour toutes les personnes contactées par l'entreprise, qu'elles soient associées à des clients, des prospects, des partenaires, ou d'autres entités. Il vise à faciliter le suivi des interactions, la communication et la gestion des relations professionnelles. Une fonctionnalité clé est la possibilité de synchroniser les contacts avec Google Contacts.

## 2. Composants Clés et Fonctionnalités

*   **Interface de Gestion des Contacts (`contact_manager/contact_list_widget.py`)**:
    *   **Affichage de la Liste des Contacts**: Tableau ou liste présentant les contacts avec des informations clés (Nom, Prénom, Société associée, E-mail, Téléphone, Fonction).
    *   **Fonctionnalités de Tri et de Filtrage**: Permettre de trier la liste par différentes colonnes et de filtrer les contacts (par société, par tags/catégories, etc.).
    *   **Recherche Rapide**: Champ de recherche pour trouver un contact par son nom, sa société, son e-mail.
    *   **Actions sur les Contacts**: Boutons ou menus contextuels pour :
        *   Ajouter un nouveau contact.
        *   Modifier un contact existant.
        *   Supprimer un contact.
        *   Visualiser les détails complets d'un contact.
        *   Lier un contact à une société cliente existante ou en créer une nouvelle.
        *   Initier une communication (envoyer un e-mail, appeler - si intégration téléphonique).

*   **Dialogues de Gestion des Contacts (`dialogs/contact_dialog.py`)**:
    *   Interface modale pour la création et la modification d'un contact. Elle devrait comprendre des champs pour :
        *   Informations personnelles (civilité, nom, prénom, fonction/titre).
        *   Société à laquelle le contact est rattaché.
        *   Coordonnées multiples (e-mails professionnels/personnels, numéros de téléphone fixe/mobile/fax).
        *   Adresses.
        *   Notes et commentaires sur le contact.
        *   Source du contact, date du premier contact.
        *   Tags ou catégories pour segmenter les contacts.

*   **Synchronisation avec Google Contacts**:
    *   **`contact_manager/google_auth.py`**: Gère le processus d'authentification OAuth2 avec Google pour autoriser l'application à accéder aux contacts de l'utilisateur.
    *   **`contact_manager/google_people_api.py`**: Contient la logique pour interagir avec l'API Google People (lecture, création, mise à jour des contacts Google).
    *   **`contact_manager/google_settings_dialog.py`**: Interface pour configurer les paramètres de synchronisation avec Google Contacts (compte Google à utiliser, fréquence de synchronisation, sens de la synchronisation - bidirectionnelle, unidirectionnelle).
    *   **`contact_manager/sync_service.py`**: Service ou thread en arrière-plan qui effectue la synchronisation effective des contacts entre la base de données locale de ClientDocManager et Google Contacts. Gère la détection des changements, la résolution des conflits (potentiellement).
    *   Interaction avec `db/cruds/google_sync_crud.py` pour stocker l'état de la synchronisation, les tokens, etc.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/contacts_crud.py`**: Fonctions CRUD pour créer, lire, mettre à jour, et supprimer les contacts dans la base de données locale.
    *   **`db/models/contacts.py`**: Définition SQLAlchemy de la table des contacts.
    *   **`db/cruds/google_sync_crud.py`**: Pour stocker les informations relatives à la synchronisation Google (tokens d'accès/refresh, date de dernière synchronisation, mapping d'ID, etc.).

## 3. Flux de Travail Typique

### 3.1. Ajout d'un Nouveau Contact Manuel

1.  L'utilisateur accède à l'interface de gestion des contacts et clique sur "Ajouter Contact".
2.  Le `ContactDialog` s'ouvre.
3.  L'utilisateur remplit les informations du contact (nom, société, e-mail, téléphone, etc.).
4.  L'utilisateur valide le dialogue.
5.  La logique du dialogue (ou un contrôleur associé) récupère les données.
6.  `contacts_crud.add_contact()` est appelé pour insérer le nouveau contact dans la base de données locale.
7.  L'interface de gestion des contacts est rafraîchie.

### 3.2. Synchronisation Initiale avec Google Contacts

1.  L'utilisateur accède aux paramètres de synchronisation Google via `GoogleSettingsDialog`.
2.  L'utilisateur initie le processus d'authentification via `google_auth.py`. Cela implique généralement d'ouvrir un navigateur pour que l'utilisateur se connecte à son compte Google et autorise l'application.
3.  Une fois l'autorisation obtenue, les tokens sont stockés (via `google_sync_crud`).
4.  L'utilisateur configure les options de synchronisation (par exemple, synchronisation bidirectionnelle).
5.  Le `SyncService` est démarré. Il récupère les contacts de Google via `google_people_api.py` et les contacts locaux via `contacts_crud.py`.
6.  Il compare les listes, identifie les nouveaux contacts, les contacts modifiés, et effectue les créations/mises à jour nécessaires des deux côtés (local et Google) pour aligner les deux répertoires. La gestion des conflits peut être basique (par exemple, le plus récent l'emporte) ou plus sophistiquée.

### 3.3. Consultation et Utilisation d'un Contact

1.  L'utilisateur recherche ou sélectionne un contact dans la liste.
2.  Les détails du contact s'affichent.
3.  L'utilisateur peut choisir d'envoyer un e-mail (ce qui pourrait ouvrir le client e-mail par défaut avec l'adresse du contact pré-remplie via le [Module Gestion des E-mails](./module_gestion_emails.md)) ou de voir les interactions passées (si cette fonctionnalité est implémentée).

## 4. Interactions avec d'Autres Modules

*   **Gestion des Clients**: Les contacts sont souvent des employés ou des représentants des entreprises clientes. Un contact peut être lié à une ou plusieurs fiches clients.
*   **Gestion des Documents / Facturation**: L'adresse e-mail d'un contact peut être utilisée comme destinataire principal pour l'envoi de devis, factures, etc.
*   **Gestion des E-mails**: Le module de gestion des contacts fournit les adresses e-mail pour le module d'envoi d'e-mails.
*   **Authentification et Gestion des Utilisateurs**: Distinguer les "contacts" (externes à l'entreprise) des "utilisateurs" (internes qui utilisent l'application).
*   **Base de Données**: Toutes les informations des contacts locaux et les données de synchronisation Google sont stockées et gérées via la couche d'accès aux données.

## 5. Points d'Attention

*   **Doublons**: La gestion des contacts en double est un défi courant, surtout avec la synchronisation. Des mécanismes de détection et de fusion de doublons sont souhaitables.
*   **Qualité des Données**: Maintenir des informations de contact exactes et à jour.
*   **Permissions Google API**: L'application doit demander uniquement les permissions (scopes) nécessaires pour accéder aux contacts Google et informer clairement l'utilisateur de l'utilisation de ses données.
*   **Gestion des Erreurs de Synchronisation**: Fournir des retours clairs à l'utilisateur en cas d'échec de la synchronisation et des outils pour résoudre les problèmes.
*   **Performance de la Synchronisation**: Pour un grand nombre de contacts, la synchronisation doit être optimisée pour ne pas bloquer l'application et pour minimiser l'utilisation des quotas de l'API Google.
*   **Confidentialité des Données**: Les informations de contact peuvent être sensibles.
*   **Interface de Résolution des Conflits**: Pour une synchronisation bidirectionnelle, une interface permettant à l'utilisateur de résoudre manuellement les conflits de données (par exemple, si un contact a été modifié différemment localement et sur Google depuis la dernière synchronisation) peut être nécessaire.
