# Chapitre 4 : Gestion des Produits et Services

Que votre entreprise vende des biens physiques ou des prestations de services, le module "Produits" (ou "Catalogue", "Articles", "Services") de ClientDocManager est l'endroit où vous définissez et gérez tout ce que vous proposez à vos clients. Ce chapitre explique comment utiliser ce module.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 4.1. Accéder au Module Produits/Services

Pour accéder au module de gestion des produits ou services :

1.  Repérez le **Volet de Navigation Principal** (généralement sur le côté gauche de la fenêtre principale).
2.  Cliquez sur l'icône ou le libellé **Produits**, **Services**, **Catalogue**, ou un terme similaire.
3.  La **Zone d'Affichage Principale** se mettra à jour pour afficher la liste de vos produits et services.

## 4.2. L'Interface du Module Produits/Services

L'interface de ce module ressemble souvent à celle du module Clients :

*   **Liste des Produits/Services**:
    *   Un tableau affichant vos articles. Chaque ligne représente un produit/service et chaque colonne une information clé (ex: Référence/SKU, Nom, Catégorie, Prix de Vente, Unité, Stock actuel si applicable).
    *   **Barre de recherche**: Pour rechercher rapidement un article par son nom, sa référence, etc.
    *   **Options de tri**: Cliquez sur les en-têtes de colonnes pour trier.
    *   **Options de filtrage**: Pour affiner la liste (ex: par catégorie de produits, par statut de disponibilité).
*   **Barre d'Outils Spécifique**:
    *   Des boutons pour les actions courantes :
        *   **Nouveau Produit/Service**: Pour créer une nouvelle fiche article.
        *   **Modifier**: Pour éditer l'article sélectionné.
        *   **Supprimer**: Pour enlever l'article sélectionné (avec confirmation).
        *   **Dupliquer**: Pour créer une copie d'un article existant, utile si vous avez des produits similaires.
*   **Gestion des Catégories (Potentiel)**:
    *   Un bouton ou une section pour gérer les catégories de produits/services, vous permettant de mieux organiser votre catalogue.

## 4.3. Créer un Nouveau Produit ou Service

1.  Dans le module Produits/Services, cliquez sur le bouton **Nouveau Produit/Service**.
2.  La fenêtre (dialogue) **Ajouter un Nouveau Produit/Service** s'ouvrira.
3.  Remplissez les informations demandées. Les champs courants incluent :
    *   **Informations de base**:
        *   `Nom du Produit/Service`: Le nom commercial de l'article.
        *   `Référence` ou `SKU`: Un identifiant unique pour l'article.
        *   `Description courte`: Pour les listes ou les lignes de facture.
        *   `Description longue/détaillée`: Pour les fiches produits complètes ou les devis.
    *   **Catégorie**: Sélectionnez une catégorie pour classer l'article.
    *   **Type**: Produit physique, Service, Actif numérique, etc.
    *   **Prix**:
        *   `Prix de Vente (HT)`: Le prix hors taxes auquel vous vendez l'article.
        *   `Prix d'Achat (HT)`: Le coût d'acquisition (si vous l'achetez pour le revendre ou s'il s'agit d'un composant).
        *   `Taux de TVA applicable`: Sélectionnez le taux de taxe approprié.
    *   **Unité de mesure**: (Ex: Pièce, Heure, Jour, kg, Litre, m²).
    *   **Gestion du Stock (pour les produits physiques)**:
        *   `Quantité en stock`: Niveau de stock actuel.
        *   `Seuil d'alerte de stock bas`: Pour être notifié quand le stock est bas.
        *   `Emplacement de stockage`.
    *   **Fournisseur par défaut** (si applicable).
    *   **Images et Médias**: Option pour lier des images du produit, des fiches techniques PDF (voir [Module Gestion des Médias](./module_gestion_medias.md)).
    *   **Dimensions/Poids** (pour les produits physiques, utile pour la logistique).
    *   **Notes internes**.
4.  Cliquez sur **OK** ou **Enregistrer** pour sauvegarder le nouvel article.

## 4.4. Rechercher un Produit/Service

Utilisez le champ **Recherche** situé au-dessus de la liste des articles.
1.  Cliquez dans le champ de recherche.
2.  Tapez le nom, la référence, ou une partie de la description.
3.  La liste se filtrera pour afficher les résultats correspondants.

## 4.5. Modifier un Produit/Service

1.  **Sélectionnez l'article** dans la liste.
2.  Cliquez sur le bouton **Modifier**.
3.  La fenêtre **Modifier Produit/Service** s'ouvrira, pré-remplie avec les informations actuelles.
4.  Apportez les modifications souhaitées.
5.  Cliquez sur **OK** ou **Enregistrer**.

## 4.6. Supprimer un Produit/Service

**Attention**: Supprimer un produit/service peut avoir des conséquences s'il est utilisé dans des documents existants (devis, factures, commandes) ou des projets. L'application pourrait vous empêcher de le supprimer ou vous proposer de l'archiver/désactiver à la place.

1.  **Sélectionnez l'article** à supprimer.
2.  Cliquez sur le bouton **Supprimer**.
3.  Confirmez votre choix dans la boîte de dialogue de confirmation.

## 4.7. Gérer les Catégories de Produits/Services

Si cette fonctionnalité est disponible :
1.  Recherchez un bouton ou une option de menu comme **Gérer les Catégories**.
2.  Un dialogue s'ouvrira vous permettant d'**Ajouter**, **Modifier**, ou **Supprimer** des catégories.
3.  Ces catégories seront ensuite disponibles dans la liste déroulante "Catégorie" lors de la création ou de la modification d'un produit/service.

## 4.8. Consulter les Détails d'un Produit/Service

En plus de la modification, il peut y avoir une option pour simplement **Visualiser les détails** d'un produit sans ouvrir le mode édition. Cette vue pourrait inclure :
*   Toutes les informations de base.
*   L'historique des prix (si géré).
*   Les niveaux de stock et les mouvements (si géré).
*   Les documents où ce produit a été utilisé.
*   Les projets liés.

Ce module est essentiel pour construire vos offres commerciales et assurer la cohérence de votre catalogue. Une bonne gestion de vos produits et services simplifiera grandement la création de documents et l'analyse de vos ventes.
