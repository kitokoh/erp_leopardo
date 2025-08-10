# Module : Gestion des Produits (Desktop)

## 1. Objectif Principal

Le module de Gestion des Produits de ClientDocManager a pour but de permettre une gestion centralisée et détaillée du catalogue de produits ou services offerts par l'entreprise. Cela inclut la création, la modification, l'organisation et la consultation des informations relatives à chaque produit, facilitant ainsi leur utilisation dans d'autres modules comme la génération de documents (devis, factures) et la gestion de projet.

## 2. Composants Clés et Fonctionnalités

*   **Interface de Gestion des Produits (`product_management/page.py`)**:
    *   **Affichage de la Liste des Produits**: Un tableau ou une liste présentant les produits et services avec des informations clés (Référence/SKU, Nom, Catégorie, Prix de Vente, Stock si applicable).
    *   **Fonctionnalités de Tri et de Filtrage**: Permettre de trier la liste par différentes colonnes et de filtrer les produits (par catégorie, par statut, etc.).
    *   **Recherche Rapide**: Champ de recherche pour trouver un produit par son nom, sa référence, ou d'autres attributs.
    *   **Actions sur les Produits**: Boutons ou menus contextuels pour :
        *   Ajouter un nouveau produit/service.
        *   Modifier un produit/service existant.
        *   Supprimer un produit/service (avec confirmation et gestion des dépendances).
        *   Dupliquer un produit/service.
        *   Visualiser les détails complets d'un produit.
        *   Gérer les équivalences de produits.
    *   **Gestion des Catégories de Produits**: Possibilité de créer et d'assigner des catégories pour organiser le catalogue.

*   **Dialogues de Gestion des Produits**:
    *   **`product_management/list_dialog.py`**: Potentiellement une vue alternative ou un sélecteur de produits sous forme de dialogue.
    *   **`product_management/edit_dialog.py`** (ou un nom similaire comme `dialogs/product_dialog.py` qui semble plus générique et est présent à la racine `dialogs/`): Interface modale pour la création et la modification d'un produit. Elle devrait comprendre des champs pour :
        *   Informations de base (nom, référence/SKU, description courte et longue).
        *   Catégorisation.
        *   Prix (prix d'achat, prix de vente, gestion de différentes devises ou tarifs).
        *   Unité de mesure (pièce, heure, kg, etc.).
        *   Informations fiscales (taux de TVA applicable).
        *   Gestion du stock (quantité en stock, seuil d'alerte, si applicable).
        *   Fournisseur(s) par défaut.
        *   Images du produit (`product_media_links_crud.py` suggère la liaison à des médias).
        *   Dimensions, poids (utile pour la logistique, `product_dimension_ui_dialog.py`).
        *   Champs personnalisés.
    *   **`dialogs/manage_product_master_dialog.py`**: Suggère une gestion plus avancée ou une vue "maître" des produits.
    *   **`dialogs/product_equivalency_dialog.py`**: Interface pour définir et gérer les produits équivalents ou de remplacement.
    *   **`dialogs/edit_product_line_dialog.py`**: Pourrait être lié à la modification d'une ligne de produit dans un document (devis, facture), ajustant quantité, prix, remise pour cette instance spécifique.

*   **Gestion des Médias Produits**:
    *   Liaison d'images, fiches techniques PDF, ou autres fichiers médias à un produit (via `db/cruds/product_media_links_crud.py` et `db/cruds/media_items_crud.py`).

*   **Gestion de Stock (Optionnelle mais suggérée par `internal_stock_items_crud.py`)**:
    *   Suivi des quantités en stock.
    *   Mouvements de stock (entrées, sorties).
    *   Alertes de stock bas.
    *   Localisation des items en stock (`item_locations_crud.py`).

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/products_crud.py`**: Fonctions CRUD pour créer, lire, mettre à jour, et supprimer les produits dans la base de données.
    *   **`db/cruds/product_media_links_crud.py`**: Gère les liaisons entre produits et fichiers médias.
    *   **`db/cruds/internal_stock_items_crud.py`**, **`db/cruds/item_locations_crud.py`**: CRUDs pour la gestion des stocks et localisations.
    *   **`db/models/products.py`** (et autres modèles liés comme `product_media_link.py`, `internal_stock_item.py`) : Définitions SQLAlchemy des tables correspondantes.

## 3. Flux de Travail Typique

### 3.1. Ajout d'un Nouveau Produit

1.  L'utilisateur accède à l'interface de gestion des produits et clique sur "Ajouter Produit".
2.  Le dialogue de création/édition de produit (`product_dialog.py` ou `product_management/edit_dialog.py`) s'ouvre.
3.  L'utilisateur remplit les informations du produit (nom, référence, prix, catégorie, description, etc.). Il peut également lier des images ou d'autres médias.
4.  L'utilisateur valide le dialogue.
5.  La logique du dialogue (ou un contrôleur associé) récupère les données saisies.
6.  Les données sont validées.
7.  `products_crud.add_product()` (ou une fonction de service équivalente) est appelée pour insérer le nouveau produit en base de données. Les informations liées (médias, stock initial) sont également enregistrées via leurs CRUDs respectifs.
8.  L'interface de gestion des produits est rafraîchie pour afficher le nouveau produit.

### 3.2. Modification d'un Produit

1.  L'utilisateur sélectionne un produit dans la liste et choisit de le modifier.
2.  Le dialogue de création/édition de produit s'ouvre, pré-rempli avec les données du produit existant.
3.  L'utilisateur modifie les informations souhaitées.
4.  Après validation, `products_crud.update_product()` est appelé.
5.  La base de données est mise à jour.
6.  L'interface est rafraîchie.

## 4. Interactions avec d'Autres Modules

*   **Gestion Client (pour la partie documents)**: Les produits sont sélectionnés et ajoutés aux documents commerciaux (devis, factures proforma, factures, bons de commande) gérés via le module "Gestion Client". Les informations du produit (description, prix) sont utilisées pour remplir ces documents.
*   **Facturation et Paiements**: Les lignes de facture sont basées sur les produits/services vendus.
*   **Gestion de Projet**: Les produits ou services peuvent être des livrables ou des composants d'un projet. `client_project_products_crud.py` suggère une liaison directe.
*   **Gestion des Actifs/Inventaire**: Si les produits sont des actifs suivis, ce module interagit étroitement. La gestion de stock est une composante de cela.
*   **Rapports et Statistiques**: Les données sur les ventes de produits, la performance des produits, les niveaux de stock sont essentielles pour les rapports.
*   **Base de Données**: Toutes les informations des produits sont stockées et gérées via la couche d'accès aux données.

## 5. Points d'Attention

*   **Structure du Catalogue**: Une bonne structuration du catalogue (catégories, références claires) est essentielle pour une utilisation efficace.
*   **Gestion des Prix**: La complexité de la gestion des prix (multi-devises, tarifs clients spécifiques, promotions) peut varier. L'application doit être claire sur ce qu'elle supporte.
*   **Gestion des Stocks**: Si la gestion des stocks est implémentée, elle doit être précise et fiable pour éviter les ruptures ou les surstocks.
*   **Dépendances**: La suppression d'un produit doit être gérée avec soin si ce produit est utilisé dans des documents historiques ou des projets en cours (par exemple, permettre l'archivage plutôt que la suppression).
*   **Import/Export de Données**: Pour les catalogues volumineux, des fonctionnalités d'import/export (par exemple, depuis CSV/Excel) peuvent être très utiles.
*   **Performance**: L'affichage et la recherche dans un grand catalogue de produits doivent rester performants.
