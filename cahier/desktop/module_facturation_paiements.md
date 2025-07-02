# Module : Facturation et Paiements (Desktop)

## 1. Objectif Principal

Le module de Facturation et Paiements de ClientDocManager est crucial pour la gestion financière des ventes et des services. Son objectif est de permettre la création précise et professionnelle de factures (proforma et finales), d'enregistrer les paiements reçus, de suivre les soldes clients, et potentiellement de gérer certains aspects comptables de base liés aux revenus et dépenses de l'entreprise.

## 2. Composants Clés et Fonctionnalités

*   **Gestion des Factures (`invoicing/`)**:
    *   **`invoicing/invoice_management_widget.py`**: Interface principale pour visualiser et gérer les factures.
        *   Liste des factures (proforma et finales) avec des informations clés (Numéro, Client, Date, Montant Total, Statut - Brouillon, Envoyée, Payée, Partiellement Payée, En Retard).
        *   Fonctionnalités de tri, filtrage (par client, statut, date) et recherche de factures.
        *   Actions : Créer une nouvelle facture, modifier une facture (si statut le permet), visualiser, dupliquer, supprimer/annuler, marquer comme envoyée, enregistrer un paiement.
    *   **Création de Factures**:
        *   Possibilité de créer une facture à partir de zéro.
        *   Possibilité de convertir une facture proforma existante en facture finale.
        *   Sélection du client, ajout de produits/services (avec quantités, prix, remises, TVA).
        *   Calcul automatique des totaux, sous-totaux, taxes.
        *   Gestion des conditions de paiement, dates d'échéance.
        *   Numérotation automatique et personnalisable des factures.
    *   **`invoicing/manual_invoice_dialog.py`**: Dialogue pour la création/édition manuelle d'une facture.
    *   **`invoicing/invoice_details_dialog.py`**: Pour afficher les détails complets d'une facture.
    *   **`invoicing/final_invoice_data_dialog.py`**: Potentiellement un dialogue pour confirmer/compléter les informations avant de finaliser une facture.
    *   **Génération du PDF de la Facture**: Utilise le [Module de Gestion des Documents](./module_gestion_documents.md) avec des modèles spécifiques pour les factures.

*   **Gestion des Factures Proforma**:
    *   Fonctionnalités similaires à la gestion des factures finales, mais pour les documents non comptables que sont les proformas.
    *   Logique de création et de gestion potentiellement dans `proforma_invoice_utils.py`.
    *   Liaison avec `db/cruds/proforma_invoices_crud.py`.

*   **Enregistrement des Paiements**:
    *   **`invoicing/record_payment_dialog.py`**: Dialogue pour enregistrer un paiement reçu pour une ou plusieurs factures.
        *   Sélection de la facture concernée.
        *   Date du paiement, montant payé, mode de paiement (virement, chèque, espèces, etc.), référence du paiement.
        *   Gestion des paiements partiels.
    *   Mise à jour automatique du statut de la facture (Payée, Partiellement Payée) et du solde dû par le client.
    *   Interaction avec `db/cruds/payments_crud.py` (s'il existe, sinon via `invoices_crud.py`).

*   **Suivi des Échéances et Relances**:
    *   Identification des factures en retard.
    *   Fonctionnalités pour envoyer des rappels de paiement (potentiellement via le [Module Gestion des E-mails](./module_gestion_emails.md)).

*   **Aspects Comptables (`accounting/`)**:
    *   **`accounting/api.py`**, **`accounting/cruds.py`**, **`accounting/models.py`**: Suggèrent la gestion d'éléments comptables.
    *   **Gestion des Dépenses de l'Entreprise (`company_expenses_api.py`, `company_expenses_crud.py`)**: Enregistrement et catégorisation des dépenses de l'entreprise.
    *   **Gestion des Factures Fournisseurs (`company_factures_api.py`)**: Enregistrement et suivi des factures reçues des fournisseurs.
    *   Potentiellement, génération de rapports comptables de base (journal des ventes, suivi des dépenses).

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/invoices_crud.py`**: CRUD pour les factures finales.
    *   **`db/cruds/proforma_invoices_crud.py`**: CRUD pour les factures proforma.
    *   **`db/cruds/payments_crud.py`** (ou logique intégrée dans `invoices_crud.py`): Pour les paiements.
    *   **`db/cruds/company_expenses_crud.py`**: CRUD pour les dépenses.
    *   **`db/models/invoices.py`**, **`db/models/payments.py`**, **`db/models/company_expenses.py`**: Définitions SQLAlchemy des tables.

## 3. Flux de Travail Typique

### 3.1. Création et Envoi d'une Facture

1.  L'utilisateur initie la création d'une facture depuis `InvoiceManagementWidget` ou convertit une proforma.
2.  Le `ManualInvoiceDialog` (ou un dialogue similaire) s'ouvre.
3.  L'utilisateur sélectionne un client, ajoute des lignes de produits/services, vérifie les conditions de paiement et la date d'échéance.
4.  Le système calcule les totaux et les taxes.
5.  L'utilisateur valide. La facture est enregistrée en base de données (via `invoices_crud.add_invoice()`) avec un statut "Brouillon" ou "Finalisée".
6.  L'utilisateur choisit de générer le PDF de la facture. Le [Module de Gestion des Documents](./module_gestion_documents.md) est sollicité.
7.  L'utilisateur peut ensuite marquer la facture comme "Envoyée" et l'envoyer au client (par e-mail via le module concerné).

### 3.2. Enregistrement d'un Paiement Client

1.  Depuis `InvoiceManagementWidget`, l'utilisateur sélectionne une facture impayée ou partiellement payée et choisit "Enregistrer Paiement".
2.  Le `RecordPaymentDialog` s'ouvre.
3.  L'utilisateur saisit la date du paiement, le montant payé, le mode de paiement et une référence.
4.  Après validation, le paiement est enregistré en base de données (via `payments_crud.add_payment()` ou une méthode de `invoices_crud`).
5.  Le statut de la facture est mis à jour (par exemple, "Payée" ou "Partiellement Payée").
6.  Le solde dû par le client est mis à jour.

### 3.3. Enregistrement d'une Dépense

1.  L'utilisateur accède à la section de gestion des dépenses (si l'interface existe, sinon via une API ou un import).
2.  Il saisit les détails de la dépense : date, montant, fournisseur, catégorie, description, justificatif.
3.  La dépense est enregistrée via `company_expenses_crud.add_expense()`.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Clients**: Les factures sont émises pour des clients spécifiques. Le module récupère les informations du client (adresse de facturation, conditions de paiement par défaut).
*   **Gestion des Produits**: Les lignes de facture sont composées de produits ou services du catalogue, avec leurs prix et descriptions.
*   **Gestion des Documents**: Utilisé pour générer les représentations PDF des factures et proformas.
*   **Paramètres et Configuration**: Configure les taux de TVA par défaut, les formats de numérotation des factures, les modèles de facture, les informations de l'entreprise pour l'en-tête des factures.
*   **Gestion des E-mails**: Pour envoyer les factures et les rappels de paiement aux clients.
*   **Rapports et Statistiques**: Les données de facturation et de paiement sont fondamentales pour les rapports financiers (chiffre d'affaires, soldes clients, analyse des revenus et dépenses).
*   **Base de Données**: Stocke toutes les données de facturation, paiements, et dépenses.

## 5. Points d'Attention

*   **Conformité Légale**: Les factures doivent respecter les obligations légales du pays (mentions obligatoires, calcul des taxes, numérotation séquentielle).
*   **Précision des Calculs**: Les calculs de totaux, taxes, remises doivent être rigoureusement exacts.
*   **Sécurité des Données Financières**: Les informations de facturation et de paiement sont sensibles.
*   **Non-Répudiation**: Assurer l'intégrité des factures une fois finalisées (par exemple, empêcher les modifications après envoi, sauf via des avoirs).
*   **Gestion des Avoirs**: Fonctionnalité pour créer des notes de crédit (avoirs) en cas de retours, d'erreurs de facturation.
*   **Export Comptable**: Possibilité d'exporter les données de facturation et de paiement dans un format compatible avec les logiciels de comptabilité (CSV, Excel, ou formats spécifiques).
*   **Multi-Devises**: Si l'entreprise opère à l'international, la gestion de multiples devises pour la facturation et les paiements est nécessaire.
