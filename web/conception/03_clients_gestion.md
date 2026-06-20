# Module : Gestion des Clients

## 1. Introduction et Objectifs

Ce module est dédié à la gestion des informations clients. Chaque client est rattaché à une "Société" (compte entreprise) spécifique. Les utilisateurs peuvent créer, consulter, mettre à jour et supprimer des fiches clients dans le contexte de leur société active.

**Objectifs Clés :**

*   Permettre la création de nouvelles fiches clients.
*   Afficher une liste paginée et filtrable des clients.
*   Permettre la consultation détaillée des informations d'un client.
*   Permettre la modification des informations d'un client.
*   Permettre la suppression d'un client (avec les précautions nécessaires).
*   Associer les clients à la société active de l'utilisateur.

## 2. Modèles de Données Associés

*   **`clients.Client`** (Défini dans `00_architecture_globale.md` et rappelé ici)
    *   `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
    *   `created_at = models.DateTimeField(auto_now_add=True)`
    *   `updated_at = models.DateTimeField(auto_now=True)`
    *   `company_account = models.ForeignKey(Company, related_name='clients', on_delete=models.CASCADE)` : La société à laquelle ce client est rattaché.
    *   `client_name = models.CharField(max_length=255)` : Nom du client (entreprise ou particulier).
    *   `email = models.EmailField(null=True, blank=True)` : Email principal du client.
    *   `phone = models.CharField(max_length=50, null=True, blank=True)` : Téléphone principal.
    *   `address = models.TextField(null=True, blank=True)` : Adresse postale.
    *   `contact_person_name = models.CharField(max_length=200, null=True, blank=True)` : Nom de la personne de contact principale.
    *   `contact_person_email = models.EmailField(null=True, blank=True)`
    *   `contact_person_phone = models.CharField(max_length=50, null=True, blank=True)`
    *   `notes = models.TextField(null=True, blank=True)` : Notes internes sur le client.
    *   `is_active = models.BooleanField(default=True)` : Pour désactiver un client sans le supprimer.
*   **`users.Company`** : La société propriétaire du client.
*   **`documents.Document`** : Les clients auront des documents associés (lien via `ForeignKey` depuis `Document` vers `Client`).

## 3. Spécifications de l'API (Endpoints DRF pertinents)

Détails dans `06_api_specifications_drf.md`. Résumé pour les clients :

*   **`GET /api/clients/`** : Lister tous les clients de la société active de l'utilisateur. Permet le filtrage et la pagination.
*   **`POST /api/clients/`** : Créer un nouveau client pour la société active.
*   **`GET /api/clients/<client_id>/`** : Récupérer les détails d'un client spécifique.
*   **`PUT /api/clients/<client_id>/`** : Mettre à jour un client.
*   **`PATCH /api/clients/<client_id>/`** : Mettre à jour partiellement un client.
*   **`DELETE /api/clients/<client_id>/`** : Supprimer un client.

L'API s'assurera que toutes les opérations sont effectuées dans le contexte de la `company_account` de l'utilisateur (ou de la société active sélectionnée).

## 4. Fonctionnalités Détaillées

Pour toutes les fonctionnalités suivantes, il est implicite que les opérations sont effectuées dans le contexte de la **société active** de l'utilisateur connecté. La vue Django ou l'API DRF doit s'assurer de ce filtrage.

### 4.1. Créer un Nouveau Client

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur gestionnaire de clients, je veux ajouter une nouvelle fiche client avec ses informations de base pour pouvoir ensuite lui associer des documents."
*   **Préconditions** : Utilisateur connecté, ayant une société active sélectionnée et les permissions de créer des clients dans cette société.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur un bouton "Nouveau Client" ou "Ajouter un Client" (généralement depuis la liste des clients).
    2.  **Interface Utilisateur (Page `/clients/add/`)** :
        *   **URL** : `/clients/add/`
        *   **Template** : `clients/client_form.html`
        *   **Formulaire** (basé sur `clients.forms.ClientForm`):
            *   Champ "Nom du client" (`client_name`): Texte, requis.
            *   Champ "Email" (`email`): Email, optionnel, validation de format.
            *   Champ "Téléphone" (`phone`): Texte, optionnel.
            *   Champ "Adresse" (`address`): Textarea, optionnel.
            *   Champ "Nom du contact" (`contact_person_name`): Texte, optionnel.
            *   Champ "Email du contact" (`contact_person_email`): Email, optionnel.
            *   Champ "Téléphone du contact" (`contact_person_phone`): Texte, optionnel.
            *   Champ "Notes" (`notes`): Textarea, optionnel.
            *   Bouton "Enregistrer le client".
    3.  **Logique Backend (Vue Django `clients.views.ClientCreateView`)** :
        *   Méthode `GET` : Affiche le formulaire `ClientForm` vide.
        *   Méthode `POST` :
            *   Récupère `active_company_id` depuis la session de l'utilisateur. Si non défini, rediriger vers la sélection de société ou afficher une erreur.
            *   Valide les données du formulaire soumis avec `ClientForm`.
            *   Si valide :
                *   Prépare le payload JSON pour l'API, en ajoutant `company_account: active_company_id`.
                *   Appelle l'endpoint API `POST /api/clients/` avec le payload.
                *   L'API DRF (via `ClientSerializer` et `ClientViewSet`) crée l'objet `Client` en l'associant à la `company_account` fournie.
                *   Si succès de l'API : Affiche un message de succès (ex: "Client '[Nom du client]' créé."). Redirige vers la liste des clients (`/clients/`) ou la page de détail du nouveau client (`/clients/<new_client_id>/`).
            *   Si invalide ou erreur API : Ré-affiche le formulaire `client_form.html` avec les messages d'erreur.
*   **Flux Alternatifs et Exceptions** :
    *   Champs requis manquants : Erreurs de formulaire affichées.
    *   Email invalide : Erreur de formulaire.
    *   Aucune société active sélectionnée : Message d'erreur et/ou redirection.
    *   L'utilisateur n'a pas les droits de création dans la société active : Erreur 403.
*   **Postconditions** : Un nouvel objet `Client` est créé en base de données, associé à la société active de l'utilisateur.
*   **Permissions Requises** : Authentifié, droit de création de client pour la société active.

### 4.2. Afficher la Liste des Clients

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux voir la liste de tous les clients associés à ma société active pour rapidement trouver un client ou avoir une vue d'ensemble."
*   **Préconditions** : Utilisateur connecté, ayant une société active sélectionnée.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur un lien de menu "Clients".
    2.  **Interface Utilisateur (Page `/clients/`)** :
        *   **URL** : `/clients/`
        *   **Template** : `clients/client_list.html`
        *   **Affichage** :
            *   Titre : "Liste des Clients (Société : [Nom de la société active])".
            *   Bouton "Ajouter un Client".
            *   **Zone de Filtres/Recherche (HTMX)** :
                *   Champ de recherche par nom (`search_query`).
                *   (Optionnel) Filtre par statut (`is_active`).
                *   Bouton "Rechercher/Filtrer".
            *   **Tableau des Clients** (`<div id="client-table-container">...</div>` pour HTMX) :
                *   Colonnes : Nom du client, Email, Téléphone, Personne de contact, Statut (Actif/Inactif).
                *   Pour chaque client : Lien vers la vue détaillée, lien/bouton "Modifier", lien/bouton "Supprimer" (avec confirmation).
            *   **Pagination** (si grand nombre de clients, gérée par DRF et rendue par Django avec des liens HTMX).
    3.  **Logique Backend (Vue Django `clients.views.ClientListView`)** :
        *   Méthode `GET` :
            *   Récupère `active_company_id` de la session. Erreur si non trouvée.
            *   Récupère les paramètres de filtre/recherche et de page depuis `request.GET`.
            *   Appelle l'endpoint API `GET /api/clients/` en passant `company_account=active_company_id` et les paramètres de filtre/pagination.
            *   L'API retourne une liste paginée de clients.
            *   Passe les clients, les informations de pagination, et les valeurs de filtre actuelles au template `client_list.html`.
            *   Si la requête est une requête HTMX (ex: pour la recherche ou la pagination) : Rend uniquement le fragment de template du tableau (`clients/partials/client_table_fragment.html`) et le retourne.
*   **Interactions HTMX/Alpine.js** :
    *   La recherche/filtrage soumet le formulaire de filtre via HTMX (`hx-get` vers la même URL, `hx-target="#client-table-container"`, `hx-swap="outerHTML"`).
    *   Les liens de pagination utilisent HTMX de manière similaire.
*   **Flux Alternatifs et Exceptions** :
    *   Aucun client trouvé pour les filtres : Message "Aucun client ne correspond à votre recherche."
*   **Postconditions** : L'utilisateur voit la liste des clients correspondant aux critères.
*   **Permissions Requises** : Authentifié, droit de lecture des clients pour la société active.

### 4.3. Consulter les Détails d'un Client

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux voir toutes les informations détaillées d'un client spécifique, y compris son historique de documents."
*   **Préconditions** : Utilisateur connecté, ayant accès au client (client appartenant à sa société active).
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur le nom d'un client dans la liste des clients, ou redirection après création/modification.
    2.  **Interface Utilisateur (Page `/clients/<client_id>/`)** :
        *   **URL** : `/clients/<uuid:client_id>/`
        *   **Template** : `clients/client_detail.html`
        *   **Affichage** :
            *   Titre : "Détails du Client : [Nom du client]".
            *   Boutons d'action : "Modifier le Client", "Supprimer le Client", "Créer un Document pour ce Client".
            *   **Section Informations Générales** : Nom, Email, Téléphone, Adresse, Notes, Statut.
            *   **Section Personne de Contact** : Nom, Email, Téléphone du contact.
            *   **Section Historique des Documents (HTMX-loaded ou initial)** :
                *   Tableau listant les documents associés à ce client (Référence, Type, Date, Statut, Montant).
                *   Liens vers les détails de chaque document.
            *   (Optionnel) Section Activités Récentes / Journal.
    3.  **Logique Backend (Vue Django `clients.views.ClientDetailView`)** :
        *   Méthode `GET` :
            *   Récupère `client_id` de l'URL.
            *   Récupère `active_company_id` de la session.
            *   Appelle l'API `GET /api/clients/<client_id>/` (l'API doit vérifier que le client appartient à `active_company_id` ou que l'utilisateur y a accès).
            *   Si succès, récupère aussi les documents liés à ce client via un autre appel API (`GET /api/documents/?client_id=<client_id>`) ou l'API du client retourne cette information imbriquée.
            *   Passe l'objet client et la liste des documents au template.
*   **Flux Alternatifs et Exceptions** :
    *   Client non trouvé (ID incorrect ou n'appartient pas à la société active) : Erreur 404.
*   **Postconditions** : L'utilisateur voit les informations complètes du client.
*   **Permissions Requises** : Authentifié, droit de lecture du client spécifique.

### 4.4. Modifier un Client Existant

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur gestionnaire de clients, je veux modifier les informations d'une fiche client existante."
*   **Préconditions** : Utilisateur connecté, ayant les droits de modification sur le client (client appartenant à sa société active).
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur le bouton "Modifier" depuis la liste des clients ou la page de détail d'un client.
    2.  **Interface Utilisateur (Page `/clients/<client_id>/edit/`)** :
        *   **URL** : `/clients/<uuid:client_id>/edit/`
        *   **Template** : `clients/client_form.html` (le même que pour la création)
        *   **Formulaire** : `ClientForm` pré-rempli avec les données actuelles du client.
            *   Bouton "Enregistrer les modifications".
            *   Lien/bouton "Annuler" (retourne à la page de détail du client).
    3.  **Logique Backend (Vue Django `clients.views.ClientUpdateView`)** :
        *   Méthode `GET` :
            *   Récupère `client_id` et `active_company_id`.
            *   Appelle l'API `GET /api/clients/<client_id>/` pour obtenir les données du client.
            *   Initialise `ClientForm` avec ces données.
            *   Affiche le formulaire.
        *   Méthode `POST` :
            *   Récupère `client_id` et `active_company_id`.
            *   Valide les données du formulaire soumis avec `ClientForm`.
            *   Si valide :
                *   Appelle l'endpoint API `PUT /api/clients/<client_id>/` avec le payload des données modifiées (incluant `company_account: active_company_id` pour validation côté API si nécessaire, bien que l'URL contienne déjà l'ID client).
                *   Si succès de l'API : Affiche un message de succès. Redirige vers la page de détail du client (`/clients/<client_id>/`).
            *   Si invalide ou erreur API : Ré-affiche le formulaire `client_form.html` avec les erreurs.
*   **Flux Alternatifs et Exceptions** :
    *   Client non trouvé : Erreur 404.
    *   Tentative de modification d'un client d'une autre société : Erreur 403 (gérée par l'API).
*   **Postconditions** : Les informations du `Client` sont mises à jour en base de données.
*   **Permissions Requises** : Authentifié, droit de modification du client spécifique.

### 4.5. Supprimer un Client

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur gestionnaire de clients, je veux supprimer une fiche client qui n'est plus pertinente (avec confirmation)."
*   **Préconditions** : Utilisateur connecté, ayant les droits de suppression sur le client.
*   **Attention** : La suppression d'un client peut avoir des implications (ex: documents orphelins si `on_delete=SET_NULL` pour `Document.client`). La stratégie de suppression (logique vs physique, gestion des dépendances) doit être claire. Pour MVP, une suppression logique (`is_active=False`) est plus sûre. Si suppression physique, une confirmation est indispensable.
*   **Flux Nominal (Suppression Logique - `is_active=False`)** :
    1.  **Déclencheur** : Clic sur un bouton "Désactiver" ou "Archiver" (au lieu de "Supprimer").
    2.  **Interface Utilisateur** :
        *   Une modale de confirmation s'affiche : "Voulez-vous vraiment désactiver le client [Nom du client] ? Il n'apparaîtra plus dans les listes actives mais ses données seront conservées."
        *   Boutons "Confirmer la désactivation", "Annuler".
    3.  **Logique Backend (Vue Django ou action HTMX)** :
        *   Sur confirmation, envoi d'une requête (ex: `PATCH /api/clients/<client_id>/` avec `{"is_active": false}`) à l'API.
        *   L'API met à jour le champ `is_active` du client.
        *   Retour d'un message de succès. Mise à jour de la liste des clients (le client désactivé peut disparaître ou changer de style).
*   **Flux Nominal (Suppression Physique - avec confirmation)** :
    1.  **Déclencheur** : Clic sur "Supprimer" depuis la liste ou détail.
    2.  **Interface Utilisateur (Page `/clients/<client_id>/delete/` ou Modale)** :
        *   **URL (si page dédiée)** : `/clients/<uuid:client_id>/delete/`
        *   **Template (si page dédiée)** : `clients/client_confirm_delete.html`
        *   **Affichage** : Message "Voulez-vous vraiment supprimer le client [Nom du client] ? Cette action est irréversible et supprimera également tous les documents associés (si cascade)."
        *   Bouton "Oui, supprimer définitivement".
        *   Lien "Annuler".
    3.  **Logique Backend (Vue Django `clients.views.ClientDeleteView`)** :
        *   Méthode `GET` (si page dédiée) : Affiche la confirmation.
        *   Méthode `POST` (sur clic "Oui, supprimer") :
            *   Appelle l'endpoint API `DELETE /api/clients/<client_id>/`.
            *   L'API DRF supprime le client (et les données en cascade si configuré ainsi au niveau du modèle/DB).
            *   Si succès : Affiche un message de succès. Redirige vers la liste des clients (`/clients/`).
*   **Postconditions** :
    *   Suppression logique : Le client a `is_active = False`.
    *   Suppression physique : Le client (et potentiellement ses données liées) est supprimé de la base de données.
*   **Permissions Requises** : Authentifié, droit de suppression du client.

---
Ce module forme la base de la gestion des entités avec lesquelles l'entreprise interagit. La clarté de son interface et la robustesse de sa logique sont essentielles.
