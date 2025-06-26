# Module : Gestion des Médias (Centralisée - Desktop)

## 1. Objectif Principal

Le module de Gestion des Médias de ClientDocManager vise à fournir un référentiel centralisé pour stocker, organiser et gérer divers types de fichiers médias (images, documents PDF, vidéos, etc.) qui peuvent être utilisés à travers l'application. Plutôt que de dupliquer des fichiers ou de les lier de manière ad-hoc, ce module pourrait offrir une bibliothèque de médias réutilisables.

L'analyse initiale suggère l'existence de `media_manager/` et `db/cruds/media_items_crud.py` ainsi que `db/models/media_items.py`. De plus, des tables de liaison comme `product_media_link.py` et `asset_media_links.py` indiquent que les médias sont associés à d'autres entités. Ce document explore si une gestion *centralisée* distincte existe au-delà de ces liaisons.

## 2. Composants Clés et Fonctionnalités (Basées sur l'Hypothèse d'une Gestion Centralisée)

Si une gestion centralisée est implémentée via `media_manager/` :

*   **Navigateur de Médias (Interface Utilisateur dans `media_manager/`)**:
    *   Une interface pour visualiser tous les médias stockés dans la bibliothèque.
    *   Affichage sous forme de grille de vignettes ou de liste.
    *   Fonctionnalités de recherche, de filtrage (par type de fichier, tags, date d'ajout) et de tri.
    *   Actions :
        *   Télécharger de nouveaux fichiers médias.
        *   Modifier les métadonnées d'un média (titre, description, tags, copyright).
        *   Supprimer des médias (avec gestion des dépendances si un média est utilisé).
        *   Prévisualiser les médias (images, PDFs, potentiellement audio/vidéo si supporté).
        *   Organiser en dossiers ou catégories.

*   **Stockage des Fichiers Médias**:
    *   Les fichiers eux-mêmes sont stockés sur le système de fichiers du serveur ou sur un service de stockage externe (cloud). La base de données contient les métadonnées et le chemin d'accès ou l'URL du fichier.
    *   `media_manager/operations.py` pourrait contenir la logique pour la manipulation des fichiers (upload, suppression, création de vignettes).

*   **Métadonnées des Médias (`db/models/media_items.py`, `db/cruds/media_items_crud.py`)**:
    *   La table `media_items` stockerait des informations pour chaque fichier média :
        *   ID unique.
        *   Nom du fichier original.
        *   Chemin de stockage / URL.
        *   Type MIME.
        *   Taille du fichier.
        *   Titre, description, tags, texte alternatif (pour l'accessibilité).
        *   Date de création/modification.
        *   Dimensions (pour les images/vidéos).
        *   Informations de copyright.

*   **Liaison avec d'Autres Entités**:
    *   Le principal usage d'un gestionnaire de médias centralisé est de permettre de lier facilement ces médias à d'autres objets de l'application :
        *   **Produits**: Images de produits, fiches techniques PDF ([Module Gestion des Produits](./module_gestion_produits.md) via `product_media_link.py`).
        *   **Actifs**: Photos d'équipements, factures d'achat ([Module Gestion des Actifs](./module_gestion_actifs.md) via `asset_media_links.py`).
        *   **Clients/Projets**: Logos de clients, documents de projet.
        *   **Contenu d'E-mails/Documents**: Images à insérer dans les modèles.
    *   Lors de la liaison, c'est l'ID du `MediaItem` qui est stocké dans la table de liaison, évitant la duplication du fichier ou de ses métadonnées.

*   **Fonctionnalités Avancées (Potentielles)**:
    *   Traitement d'images de base (redimensionnement, recadrage, création de vignettes).
    *   Gestion des versions des médias.
    *   Contrôle d'accès aux médias (qui peut voir/utiliser quels médias).

## 3. Distinction par Rapport aux Liaisons de Médias Spécifiques

Il est important de distinguer ce module d'une simple fonctionnalité de "pièce jointe" :

*   **Pièce Jointe Simple**: Un fichier est téléchargé et directement lié à une entité spécifique (ex: un CV à un candidat). Le fichier n'est pas nécessairement destiné à être réutilisé ailleurs.
*   **Gestion Centralisée des Médias**: Les fichiers sont téléchargés dans une "bibliothèque" centrale. Ils peuvent ensuite être liés à une ou plusieurs entités. Un même média (ex: un logo d'entreprise standard) peut être réutilisé à plusieurs endroits sans être téléchargé à chaque fois.

La présence de `media_items_crud.py` et `media_manager/` suggère fortement une approche de gestion centralisée, où `media_items` est la table centrale des médias, et les tables de liaison (`*_media_links`) connectent ces `MediaItem`s aux entités spécifiques.

## 4. Flux de Travail Typique

### 4.1. Ajout d'un Nouveau Média à la Bibliothèque

1.  L'utilisateur accède au Navigateur de Médias.
2.  Il clique sur "Télécharger" et sélectionne un ou plusieurs fichiers depuis son ordinateur.
3.  `media_manager/operations.py` gère le téléchargement, déplace le fichier vers l'emplacement de stockage configuré.
4.  Pour chaque fichier, une nouvelle entrée est créée dans la table `media_items` via `media_items_crud.add_media_item()`, enregistrant le chemin, le type, et d'autres métadonnées initiales.
5.  L'utilisateur peut ensuite éditer les métadonnées (titre, description, tags).

### 4.2. Lier un Média Existant à un Produit

1.  L'utilisateur modifie une fiche produit dans le [Module Gestion des Produits](./module_gestion_produits.md).
2.  Dans la section "Images" ou "Médias" du produit, il choisit "Ajouter depuis la bibliothèque" (ou un libellé similaire).
3.  Une version simplifiée du Navigateur de Médias s'ouvre, permettant de sélectionner un `MediaItem` existant.
4.  L'utilisateur sélectionne une image.
5.  Une nouvelle entrée est créée dans la table `product_media_links` via `product_media_links_crud.add_link()`, associant l'ID du produit et l'ID du `MediaItem` sélectionné.

## 5. Interactions avec d'Autres Modules

*   **Gestion des Produits**: Utilise le gestionnaire de médias pour associer des images et des fiches techniques aux produits.
*   **Gestion des Actifs**: Utilise le gestionnaire de médias pour associer des photos, manuels, factures aux actifs.
*   **Paramètres et Configuration**: Pour définir le chemin de stockage des médias.
*   **Tous les modules nécessitant l'affichage ou l'utilisation d'images/documents stockés** (ex: insertion d'un logo d'entreprise dans un modèle de document).
*   **Base de Données**: La table `media_items` est centrale, et de nombreuses tables de liaison (`product_media_links`, `asset_media_links`, etc.) y font référence.

## 6. Points d'Attention

*   **Stockage et Volume**: La gestion de nombreux fichiers médias, surtout s'ils sont volumineux (images haute résolution, vidéos), peut nécessiter un espace de stockage important et des stratégies de sauvegarde adaptées.
*   **Performance**: L'affichage de galeries de médias et le chargement des fichiers doivent être optimisés. La génération de vignettes est essentielle pour les aperçus.
*   **Organisation**: Des fonctionnalités robustes de catégorisation, de tagging et de recherche sont nécessaires pour retrouver facilement les médias.
*   **Gestion des Doublons**: Éviter le téléchargement multiple du même fichier. Des mécanismes de détection de doublons (basés sur le hash du fichier, par exemple) peuvent être utiles.
*   **Droits d'Auteur et Licences**: Si les médias ne sont pas tous créés en interne, il peut être nécessaire de stocker des informations sur les droits d'auteur et les licences d'utilisation.
*   **Sécurité**: Contrôler qui peut télécharger, modifier ou supprimer des médias de la bibliothèque centrale.
*   **Nettoyage**: Processus pour identifier et éventuellement supprimer les médias orphelins (non liés à aucune entité active de l'application).
