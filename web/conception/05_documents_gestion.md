# Module : Gestion des Documents

## 1. Introduction et Objectifs

Ce module est au cœur de l'application et concerne la création, la consultation, la gestion et le suivi des documents commerciaux (Factures Proformas, Devis, Factures, etc.). Chaque document est rattaché à un Client spécifique, lui-même lié à une Société (compte entreprise). Les documents sont composés de lignes d'items, qui font référence aux Produits du catalogue.

**Objectifs Clés :**

*   Permettre la création de différents types de documents (Proforma en MVP).
*   Afficher une liste paginée et filtrable des documents.
*   Permettre la consultation détaillée d'un document, incluant ses lignes d'items et ses totaux.
*   Permettre la modification de documents (principalement ceux en statut "Brouillon").
*   Gérer le cycle de vie d'un document (statuts : Brouillon, Envoyé, Payé, Annulé).
*   Permettre le téléchargement du document au format PDF.
*   Associer les documents à la société active de l'utilisateur et à un client spécifique.

## 2. Modèles de Données Associés

*   **`documents.Document`** (Défini dans `00_architecture_globale.md`)
    *   `id`, `created_at`, `updated_at`
    *   `company_account = models.ForeignKey(Company, ...)`
    *   `client = models.ForeignKey(Client, ...)`
    *   `document_type = models.CharField(...)` (Choix : PROFORMA, INVOICE, QUOTE, etc.)
    *   `document_reference = models.CharField(...)` (Généré automatiquement)
    *   `issue_date = models.DateField(...)`
    *   `due_date = models.DateField(...)` (Optionnel)
    *   `total_amount_ht = models.DecimalField(...)`
    *   `total_amount_ttc = models.DecimalField(...)`
    *   `tax_rate = models.DecimalField(...)` (Taux de TVA global ou par ligne)
    *   `status = models.CharField(...)` (Choix : DRAFT, SENT, PAID, CANCELLED)
    *   `notes = models.TextField(...)` (Notes publiques sur le document)
    *   `private_notes = models.TextField(...)` (Notes internes, non visibles par le client)
    *   `created_by = models.ForeignKey(User, ...)`
    *   `currency = models.CharField(max_length=3, default='EUR')` (Optionnel, pour multi-devises)
*   **`documents.DocumentItem`** (Défini dans `00_architecture_globale.md`)
    *   `id`, `created_at`, `updated_at`
    *   `document = models.ForeignKey(Document, related_name='items', ...)`
    *   `product = models.ForeignKey(Product, ...)` (Optionnel, peut être une description libre)
    *   `description = models.CharField(...)` (Pré-remplie par produit, mais modifiable)
    *   `quantity = models.DecimalField(...)`
    *   `unit_price_ht = models.DecimalField(...)` (Prix unitaire HT)
    *   `total_item_ht = models.DecimalField(...)` (Calculé : `quantity * unit_price_ht`)
    *   `tax_rate_item = models.DecimalField(...)` (Optionnel, si TVA par ligne différente de celle du document)
*   **`users.Company`**, **`clients.Client`**, **`products.Product`**, **`users.User`**

## 3. Spécifications de l'API (Endpoints DRF pertinents)

Détails dans `06_api_specifications_drf.md`. Résumé pour les documents :

*   **`GET /api/documents/`** : Lister tous les documents de la société active. Permet filtrage (par client, type, statut, date) et pagination.
*   **`POST /api/documents/`** : Créer un nouveau document (ex: Proforma). Prend en entrée les données du document et une liste d'items.
*   **`GET /api/documents/<document_id>/`** : Récupérer les détails d'un document, incluant ses items.
*   **`PUT /api/documents/<document_id>/`** : Mettre à jour un document (principalement pour les brouillons).
*   **`PATCH /api/documents/<document_id>/`** : Mettre à jour partiellement un document (ex: changer le statut).
*   **`DELETE /api/documents/<document_id>/`** : Supprimer un document (si statut "Brouillon" ou selon règles métier).
*   **`GET /api/documents/<document_id>/download_pdf/`** : Endpoint pour générer et télécharger le PDF du document.

L'API gère la logique de calcul des totaux, la génération des références, et le versionnement/historique si nécessaire.

## 4. Fonctionnalités Détaillées

Opérations effectuées dans le contexte de la **société active** de l'utilisateur.

### 4.1. Créer une Nouvelle Facture Proforma (MVP)

*   **Cas d'Utilisation (User Story)** : "En tant qu коммерciаl, je veux créer rapidement une facture proforma pour un client, en y ajoutant des produits de mon catalogue ou des descriptions libres, afin de lui envoyer une offre."
*   **Préconditions** : Utilisateur connecté, société active sélectionnée, droits de création de documents. Client et produits existent (ou possibilité de saisie libre).
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur "Nouvelle Proforma" (ou "Nouveau Document" -> choisir type Proforma).
    2.  **Interface Utilisateur (Page `/documents/proforma/add/`)** :
        *   **URL** : `/documents/proforma/add/`
        *   **Template** : `documents/document_form.html` (adapté pour proforma)
        *   **Formulaire Principal (Informations Document)** :
            *   Champ "Client" (`client`): Select/Recherche auto-complétée (HTMX vers API `GET /api/clients/?search=...`). Requis.
            *   Champ "Date d'émission" (`issue_date`): Datepicker, défaut aujourd'hui. Requis.
            *   Champ "Date d'échéance" (`due_date`): Datepicker, optionnel.
            *   Champ "Référence" (`document_reference`): Lecture seule, sera généré par le backend.
            *   Champ "Devise" (`currency`): Select (EUR par défaut), si multi-devises.
            *   Champ "Taux de TVA Global (%)" (`tax_rate`): Nombre, défaut (ex: 20.00).
            *   Champ "Notes" (`notes`): Textarea, pour les conditions visibles par le client.
            *   Champ "Notes Privées" (`private_notes`): Textarea, pour usage interne.
        *   **Section Lignes d'Items (`DocumentItem`) - Gérée dynamiquement (Alpine.js + HTMX)** :
            *   Tableau des lignes. Chaque ligne contient :
                *   Champ "Produit/Service" (`product`): Select/Recherche auto-complétée (HTMX vers API `GET /api/products/?search=...`). La sélection d'un produit pré-remplit la description et le prix unitaire.
                *   Champ "Description" (`description`): Texte, modifiable. Requis.
                *   Champ "Quantité" (`quantity`): Nombre, défaut 1. Requis.
                *   Champ "Prix Unitaire HT" (`unit_price_ht`): Nombre. Requis.
                *   Champ "Total HT Ligne": Lecture seule, calculé (`quantity * unit_price_ht`).
            *   Bouton "Ajouter une ligne".
            *   Bouton "Supprimer la ligne" pour chaque ligne.
        *   **Section Totaux (Lecture seule, mis à jour par Alpine.js/HTMX)** :
            *   Total HT Global.
            *   Montant TVA Global.
            *   Total TTC Global.
        *   **Boutons d'Action** :
            *   "Enregistrer comme Brouillon".
            *   "Enregistrer et Marquer comme Envoyé" (si fonctionnalité de changement de statut direct).
    3.  **Logique Backend (Vue Django `documents.views.ProformaCreateView`)** :
        *   `GET` :
            *   Récupère `active_company_id`.
            *   Prépare le formulaire `DocumentForm` et un `DocumentItemFormSet` vide.
            *   Passe au template.
        *   `POST` :
            *   Récupère `active_company_id`.
            *   Valide `DocumentForm` et `DocumentItemFormSet`.
            *   Si valide :
                *   Prépare le payload JSON pour `POST /api/documents/`, incluant `company_account`, `document_type='PROFORMA'`, et la liste des `items` (chaque item avec `product_id` (si sélectionné), `description`, `quantity`, `unit_price_ht`).
                *   L'API DRF (via `DocumentSerializer`) :
                    *   Crée `Document` et ses `DocumentItem`.
                    *   Calcule `total_item_ht` pour chaque item.
                    *   Génère `document_reference`.
                    *   Appelle `document.update_totals()` pour calculer `total_amount_ht` et `total_amount_ttc`.
                    *   Définit le statut initial (ex: `DRAFT`).
                *   Si succès API : Message de succès. Redirection vers détail du document (`/documents/<new_doc_id>/`).
            *   Si erreur : Ré-affiche formulaire avec erreurs.
*   **Interactions HTMX/Alpine.js** :
    *   Recherche de clients et produits (HTMX `hx-get` sur champs input, `hx-swap` pour afficher résultats).
    *   Sélection d'un produit met à jour description et prix de la ligne (Alpine.js ou HTMX).
    *   Ajout/Suppression de lignes d'items (Alpine.js pour manipuler le DOM, ou HTMX pour recharger le formset).
    *   Calculs des totaux en temps réel (Alpine.js en écoutant les changements sur quantité/prix).
*   **Postconditions** : Nouveau `Document` (type PROFORMA) et ses `DocumentItem` créés, statut `DRAFT`.
*   **Permissions Requises** : Authentifié, droits de création de documents.

### 4.2. Afficher la Liste des Documents

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux voir la liste de tous les documents (proformas, factures, etc.) de ma société active, avec des options de filtre et de recherche."
*   **Préconditions** : Utilisateur connecté, société active sélectionnée.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur menu "Documents".
    2.  **Interface Utilisateur (Page `/documents/`)** :
        *   **URL** : `/documents/`
        *   **Template** : `documents/document_list.html`
        *   **Affichage** :
            *   Titre : "Liste des Documents (Société : [Nom société active])".
            *   Bouton "Nouveau Document" (ou "Nouvelle Proforma", etc.).
            *   **Zone de Filtres/Recherche (HTMX)** :
                *   Recherche par référence document, nom client.
                *   Filtre par `document_type` (Proforma, Facture...).
                *   Filtre par `status` (Brouillon, Envoyé...).
                *   Filtre par plage de dates (`issue_date`).
            *   **Tableau des Documents** (`<div id="document-table-container">...</div>`) :
                *   Colonnes : Référence, Type, Client, Date d'émission, Statut, Total TTC.
                *   Actions : Voir détail, Modifier (si brouillon), Télécharger PDF, Changer Statut.
            *   **Pagination**.
    3.  **Logique Backend (Vue Django `documents.views.DocumentListView`)** :
        *   `GET` : Récupère `active_company_id`, filtres, page. Appelle `GET /api/documents/` (avec `company_account`, filtres).
        *   Passe documents, pagination, options de filtre au template.
        *   Si requête HTMX : Rend fragment de tableau.
*   **Postconditions** : Liste des documents affichée.
*   **Permissions Requises** : Authentifié, droits de lecture documents.

### 4.3. Consulter les Détails d'un Document

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux voir le détail complet d'un document, y compris toutes ses lignes, les informations du client, et les totaux."
*   **Préconditions** : Utilisateur connecté, accès au document.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur une référence de document dans la liste.
    2.  **Interface Utilisateur (Page `/documents/<document_id>/`)** :
        *   **URL** : `/documents/<uuid:document_id>/`
        *   **Template** : `documents/document_detail.html` (pourrait être un template générique de "prévisualisation" du document)
        *   **Affichage** :
            *   Titre : "[Type Document] #[Référence]".
            *   Boutons d'action : "Modifier" (si brouillon), "Télécharger PDF", "Marquer comme Envoyé", "Enregistrer Paiement" (si facture), "Annuler le Document".
            *   **Informations Société Émettrice** (de `company_account`).
            *   **Informations Client** (de `document.client`).
            *   **Détails Document** : Date émission, échéance, statut, notes.
            *   **Tableau des Lignes d'Items (`DocumentItem`)** : Description, Quantité, Prix Unit. HT, Total Ligne HT.
            *   **Section Totaux** : Total HT, Montant TVA, Total TTC.
            *   (Optionnel) Historique des statuts du document.
    3.  **Logique Backend (Vue Django `documents.views.DocumentDetailView`)** :
        *   `GET` : Récupère `document_id`, `active_company_id`. Appelle `GET /api/documents/<document_id>/`.
        *   Passe l'objet document (avec ses items imbriqués) au template.
*   **Postconditions** : Détails du document affichés.
*   **Permissions Requises** : Authentifié, droits de lecture document.

### 4.4. Modifier un Document (Ex: Brouillon de Proforma)

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux modifier un document qui est encore au statut 'Brouillon'."
*   **Préconditions** : Utilisateur connecté, droits de modification, document au statut `DRAFT`.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur "Modifier" depuis détail ou liste du document.
    2.  **Interface Utilisateur (Page `/documents/<document_id>/edit/`)** :
        *   **URL** : `/documents/<uuid:document_id>/edit/`
        *   **Template** : `documents/document_form.html` (similaire à la création)
        *   **Formulaire** : `DocumentForm` et `DocumentItemFormSet` pré-remplis avec données actuelles.
    3.  **Logique Backend (Vue Django `documents.views.DocumentUpdateView`)** :
        *   `GET` : Récupère document via API, initialise formulaires. Affiche.
        *   `POST` : Valide formulaires. Si valide, appelle `PUT /api/documents/<document_id>/` avec données modifiées.
        *   L'API met à jour `Document` et ses `DocumentItem` (logique de suppression/ajout/modification des items dans le serializer DRF). Recalcule les totaux.
        *   Si succès API : Message, redirection vers détail document.
        *   Si erreur : Ré-affiche formulaire avec erreurs.
*   **Postconditions** : `Document` et `DocumentItem` mis à jour. Statut reste `DRAFT` (ou modifié par une action explicite).
*   **Permissions Requises** : Authentifié, droits de modification, statut `DRAFT`.

### 4.5. Changer le Statut d'un Document

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux changer le statut d'un document, par exemple de 'Brouillon' à 'Envoyé', ou d' 'Envoyé' à 'Payé'."
*   **Préconditions** : Utilisateur connecté, droits de modification de statut, transitions de statut valides (ex: on ne passe pas de 'Payé' à 'Brouillon').
*   **Flux Nominal (Ex: Marquer comme Envoyé)** :
    1.  **Déclencheur** : Clic sur "Marquer comme Envoyé" sur la page de détail du document.
    2.  **Interface Utilisateur** : Modale de confirmation "Voulez-vous marquer ce document comme Envoyé ? Cela pourrait le verrouiller pour modifications ultérieures."
    3.  **Logique Backend (Action HTMX ou Vue Django dédiée)** :
        *   Sur confirmation, envoi `PATCH /api/documents/<document_id>/` avec `{"status": "SENT"}`.
        *   L'API valide la transition de statut et met à jour le champ.
        *   Si succès API : Message de succès. Mise à jour de l'affichage du statut sur la page (HTMX). Certains boutons (ex: "Modifier") peuvent devenir désactivés.
*   **Logique Métier Additionnelle** :
    *   Passer à `SENT` peut impliquer la génération finale du PDF et son envoi par email (tâche asynchrone Celery).
    *   Passer à `PAID` (pour une facture) peut ouvrir un formulaire pour enregistrer les détails du paiement.
*   **Postconditions** : Statut du document mis à jour. Potentielles actions secondaires déclenchées.
*   **Permissions Requises** : Authentifié, droits spécifiques de changement de statut.

### 4.6. Télécharger le PDF d'un Document

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur, je veux télécharger une version PDF d'un document pour l'archiver ou l'envoyer à mon client."
*   **Préconditions** : Utilisateur connecté, accès au document.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : Clic sur "Télécharger PDF".
    2.  **Interface Utilisateur** : Le navigateur initie un téléchargement.
    3.  **Logique Backend (Vue Django ou lien direct vers API)** :
        *   L'action pointe vers l'endpoint API `GET /api/documents/<document_id>/download_pdf/`.
        *   L'API DRF :
            *   Récupère les données du document.
            *   Génère le contenu HTML du document en utilisant un template Jinja2/Django.
            *   Convertit cet HTML en PDF (ex: avec WeasyPrint, ReportLab, ou un service externe).
            *   Retourne une `HttpResponse` avec le contenu PDF et les en-têtes appropriés (`Content-Type: application/pdf`, `Content-Disposition: attachment; filename="proforma_XYZ.pdf"`).
*   **Postconditions** : L'utilisateur télécharge le fichier PDF.
*   **Permissions Requises** : Authentifié, droits de lecture document.

---
La gestion des documents est complexe en raison des différents types, statuts, et interactions (génération PDF, emails). Le MVP se concentrera sur les Proformas et un cycle de vie simple, avec une extension progressive. La génération de PDF est un point technique clé à bien concevoir.
