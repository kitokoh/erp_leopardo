# Module : Gestion des Partenaires (Desktop)

## 1. Objectif Principal

Le module de Gestion des Partenaires de ClientDocManager a pour but de permettre à l'entreprise d'enregistrer, de suivre et de gérer les informations relatives à ses partenaires commerciaux. Ces partenaires peuvent inclure des fournisseurs, des sous-traitants, des distributeurs, des revendeurs, des apporteurs d'affaires, ou tout autre type d'organisation avec laquelle l'entreprise collabore. L'objectif est de centraliser ces informations pour faciliter les interactions et la gestion des relations partenariales.

## 2. Composants Clés et Fonctionnalités

*   **Interface de Gestion des Partenaires (`partners/partner_main_widget.py`)**:
    *   **Affichage de la Liste des Partenaires**: Tableau ou liste présentant les partenaires enregistrés avec des informations clés (Nom du Partenaire, Type/Catégorie de Partenaire, Contact Principal, Ville, Pays).
    *   **Fonctionnalités de Tri et de Filtrage**: Permettre de trier la liste par différentes colonnes et de filtrer les partenaires (par type, par catégorie, par pays, etc.).
    *   **Recherche Rapide**: Pour trouver un partenaire par son nom ou d'autres identifiants.
    *   **Actions sur les Partenaires**:
        *   Ajouter un nouveau partenaire.
        *   Modifier les informations d'un partenaire existant.
        *   Supprimer un partenaire.
        *   Visualiser les détails complets d'un partenaire.
        *   Gérer les catégories de partenaires.

*   **Dialogues de Gestion des Partenaires**:
    *   **`partners/partner_dialog.py`**: Interface modale pour la création et la modification d'un partenaire.
        *   Champs pour : Nom de l'entreprise partenaire, forme juridique.
        *   Adresse(s), pays.
        *   Numéros d'identification (SIRET, TVA, etc.).
        *   Site web, e-mail générique de contact.
        *   Description de l'activité du partenaire.
        *   Type de partenariat (Fournisseur, Distributeur, Sous-traitant, etc.).
        *   Catégorie de partenaire (définie via `PartnerCategoryDialog`).
        *   Conditions commerciales spécifiques (si applicable).
        *   Contacts clés au sein de l'entreprise partenaire (pourraient être gérés via le [Module Gestion des Contacts](./module_gestion_contacts.md) et liés).
        *   Notes et commentaires.
    *   **`partners/partner_category_dialog.py`**: Interface pour créer, modifier et gérer les catégories de partenaires. Cela permet de classifier les partenaires de manière flexible.

*   **Informations Détaillées du Partenaire**:
    *   Une vue dédiée affichant toutes les informations d'un partenaire sélectionné, y compris :
        *   Historique des interactions ou des contrats (si cette fonctionnalité est développée).
        *   Documents liés (contrats de partenariat, accords de non-divulgation, etc.).
        *   Contacts principaux.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/partners_crud.py`**: Fonctions CRUD pour créer, lire, mettre à jour, et supprimer les partenaires et leurs catégories dans la base de données.
    *   **`db/models/partners.py`** (et `partner_categories.py` ou équivalent) : Définitions SQLAlchemy des tables correspondantes.

## 3. Flux de Travail Typique

### 3.1. Ajout d'un Nouveau Partenaire

1.  L'utilisateur accède à l'interface de gestion des partenaires (`PartnerMainWidget`) et clique sur "Ajouter Partenaire".
2.  Le `PartnerDialog` s'ouvre.
3.  L'utilisateur remplit les informations du partenaire (nom, type, catégorie, coordonnées, etc.). Si une catégorie n'existe pas, il peut avoir un raccourci pour ouvrir `PartnerCategoryDialog` et la créer.
4.  L'utilisateur valide le dialogue.
5.  La logique du dialogue (ou un contrôleur associé) récupère les données saisies.
6.  `partners_crud.add_partner()` est appelé pour insérer le nouveau partenaire dans la base de données.
7.  L'interface de gestion des partenaires est rafraîchie pour afficher le nouveau partenaire.

### 3.2. Gestion des Catégories de Partenaires

1.  L'utilisateur, depuis `PartnerMainWidget` ou `PartnerDialog`, accède à la gestion des catégories (via `PartnerCategoryDialog`).
2.  Il peut ajouter une nouvelle catégorie (ex: "Fournisseur Stratégique", "Revendeur Local"), modifier ou supprimer une catégorie existante.
3.  Ces catégories sont ensuite disponibles pour classifier les partenaires.

### 3.3. Consultation et Modification d'un Partenaire

1.  L'utilisateur sélectionne un partenaire dans la liste du `PartnerMainWidget`.
2.  Les détails du partenaire peuvent s'afficher ou l'utilisateur clique sur "Modifier".
3.  Le `PartnerDialog` s'ouvre, pré-rempli avec les données du partenaire.
4.  L'utilisateur modifie les informations et valide.
5.  `partners_crud.update_partner()` est appelé, et la base de données est mise à jour.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Produits**: Certains partenaires peuvent être des fournisseurs de produits listés dans le catalogue. Une liaison pourrait exister.
*   **Gestion des Actifs/Inventaire**: Les fournisseurs d'actifs sont des partenaires.
*   **Gestion de Projet**: Des partenaires peuvent être des sous-traitants sur des projets.
*   **Gestion Client (pour la partie documents)**: Des contrats ou d'autres documents peuvent être liés aux partenaires et gérés via le module "Gestion Client" si pertinent (par exemple, si le partenaire est aussi un client ou si le document est fortement lié à une interaction client impliquant ce partenaire). Sinon, un système de gestion documentaire spécifique aux partenaires pourrait être envisagé.
*   **Gestion des Contacts**: Les personnes de contact chez les partenaires sont gérées via le [Module Gestion des Contacts](./module_gestion_contacts.md) et peuvent être liées aux fiches partenaires.
*   **Comptabilité/Finances**: Les factures fournisseurs (si gérées dans le [Module Facturation et Paiements](./module_facturation_paiements.md) sous "Dépenses") seraient liées à des partenaires de type fournisseur.
    *   Les `client_freight_forwarders_crud.py`, `client_money_transfer_agents_crud.py`, `client_transporters_crud.py` suggèrent que des transitaires, agents de transfert d'argent, et transporteurs peuvent être des types spécifiques de partenaires, et qu'ils peuvent être liés directement à des clients pour des opérations spécifiques. Ce module "Partenaires" pourrait servir de référentiel central pour ces entités.

## 5. Points d'Attention

*   **Typologie des Partenaires**: La flexibilité dans la définition des types et catégories de partenaires est importante pour s'adapter aux différents contextes d'affaires.
*   **Qualité des Données**: Maintenir des informations exactes et à jour sur les partenaires.
*   **Suivi des Performances (Potentiel)**: Pour certains types de partenaires (fournisseurs, sous-traitants), un suivi de leur performance (qualité, respect des délais) pourrait être une extension utile.
*   **Gestion des Contrats**: Une gestion plus formelle des contrats de partenariat (dates, termes, documents) pourrait être intégrée.
*   **Visibilité et Accès**: Définir qui peut voir et modifier les informations des partenaires.
*   **Liaisons avec d'Autres Entités**: Assurer des liaisons claires et faciles à gérer entre les partenaires et d'autres objets de l'application (produits, projets, clients pour des transitaires/transporteurs spécifiques).
