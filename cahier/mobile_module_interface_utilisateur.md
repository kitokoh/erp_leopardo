# Module : Interface Utilisateur Mobile et Navigation

Ce document détaille la conception et les fonctionnalités de l'interface utilisateur principale de l'application mobile, actuellement centrée autour de l'écran de génération de documents.

## 1. Objectif Principal

L'objectif de ce module est de fournir une interface claire et intuitive permettant aux utilisateurs de sélectionner des paramètres, des produits, et de générer des documents PDF directement depuis leur appareil mobile. Il vise également à faciliter le partage de ces documents.

## 2. Écrans Principaux et Navigation

Actuellement, l'application mobile est composée d'un écran principal :

### 2.1. Écran de Génération de Documents (`DocumentGenerationScreen`)

Cet écran est le cœur de l'application mobile. Il est construit en utilisant Kivy.

**Composants et Agencement :**

L'écran est agencé verticalement (`BoxLayout`) et comprend les sections suivantes :

*   **Sélections Initiales :**
    *   **Sélecteur de Langue (`Spinner`)**: Permet à l'utilisateur de choisir la langue pour le contenu des documents et la liste des produits. La sélection de la langue actualise la liste des produits disponibles.
    *   **Sélecteur de Pays (`Spinner`)**: Permet de sélectionner un pays, potentiellement pour filtrer des informations ou des modèles spécifiques.
    *   **Sélecteur de Modèle de Document (`Spinner`)**: Permet de choisir le type de document à générer (ex: facture proforma, fiche technique).
    *   **Sélecteur d'Action PDF (`Spinner`)**: Permet de choisir si les documents pour plusieurs produits doivent être générés en tant que fichiers PDF séparés ou combinés en un seul PDF.

*   **Ajout de Produits au Document :**
    *   **Champ Quantité (`TextInput`)**: Permet de spécifier la quantité pour le produit qui sera ajouté.
    *   **Bouton "Ajouter au Document" (`Button`)**: Ajoute le produit actuellement sélectionné dans la liste des "Produits Disponibles" (avec la quantité spécifiée) à la liste des "Produits Sélectionnés pour le Document".

*   **Liste des Produits Disponibles :**
    *   Un label "Available Products:".
    *   Une zone défilante (`ScrollView` contenant un `GridLayout`) affichant les produits disponibles.
    *   Chaque produit est un bouton (`Button`) affichant son nom et son prix.
    *   Cliquer sur un produit dans cette liste le marque comme "actuellement sélectionné" pour l'ajout. Le produit sélectionné est visuellement mis en évidence.
    *   La liste est peuplée dynamiquement en fonction de la langue sélectionnée via `mobile_data_api.get_all_products_for_selection_from_api()`.

*   **Liste des Produits Sélectionnés pour le Document :**
    *   Un label "Selected Products for Document:".
    *   Une zone défilante (`ScrollView` contenant un `GridLayout`) affichant les produits qui ont été ajoutés au document.
    *   Chaque entrée montre le nom du produit et la quantité sélectionnée.
    *   Un bouton "Remove" (`Button`) est associé à chaque produit pour le retirer de la sélection.

*   **Actions sur le Document :**
    *   **Bouton "Generate & Preview PDF" (`Button`)**: Déclenche la génération du ou des PDF(s) en utilisant `LiteDocumentHandler`. Les fichiers PDF sont sauvegardés temporairement. Tente ensuite d'ouvrir/partager le premier PDF généré en utilisant `plyer.sharing`.
    *   **Bouton "Send by Email" (`Button`)**: Déclenche la génération du ou des PDF(s). Si la génération réussit, tente d'ouvrir l'application e-mail du téléphone avec les PDF en pièces jointes, en utilisant `plyer.email`.

*   **Gestion des Fichiers Temporaires :**
    *   **Bouton "Clear Temporary Files" (`Button`)**: Permet à l'utilisateur de supprimer manuellement les fichiers PDF temporaires créés par l'application.

**Indicateurs et Retours Utilisateur :**

*   **Indicateur d'Activité (`ModalView`)**: Un message "Processing, please wait..." s'affiche pendant les opérations longues (comme la génération de PDF).
*   **Popups d'Information/Erreur (`Popup`)**: Utilisées pour informer l'utilisateur des succès (ex: "PDF Generated"), des erreurs (ex: "Validation Error", "File Error"), ou des indisponibilités de fonctionnalités (ex: "Plyer email feature not implemented").

**Navigation :**

*   L'application utilise `ScreenManager` de Kivy, bien qu'actuellement un seul écran (`DocumentGenerationScreen`) soit implémenté et affiché. Cela suggère une extensibilité future pour d'autres écrans.

## 3. Technologies Utilisées

*   **Kivy (`2.0.0` ou supérieur)**: Framework principal pour l'interface utilisateur.
*   **Plyer**: Utilisé pour accéder aux fonctionnalités natives du téléphone (partage de fichiers, e-mail).
*   **Python**: Langage de programmation principal.

## 4. Flux Utilisateur Typique (pour `DocumentGenerationScreen`)

1.  L'utilisateur sélectionne une langue.
2.  La liste des produits disponibles se met à jour.
3.  L'utilisateur sélectionne un pays.
4.  L'utilisateur sélectionne un modèle de document.
5.  L'utilisateur sélectionne une action PDF (séparé/combiné).
6.  L'utilisateur parcourt la liste des produits disponibles et en sélectionne un.
7.  L'utilisateur ajuste la quantité si nécessaire.
8.  L'utilisateur clique sur "Add to Document". Le produit apparaît dans la liste des produits sélectionnés.
9.  L'utilisateur répète les étapes 6-8 pour ajouter d'autres produits.
10. L'utilisateur clique sur "Generate & Preview PDF" pour voir le document ou sur "Send by Email" pour l'envoyer.
11. L'application affiche un indicateur d'activité pendant la génération.
12. Un popup informe du résultat et, en cas de succès, tente d'ouvrir le PDF ou l'application e-mail.
13. L'utilisateur peut éventuellement cliquer sur "Clear Temporary Files" pour nettoyer l'espace de stockage.

## 5. Interactions avec d'autres modules

*   **Module de Synchronisation et Gestion des Données Mobiles**: L'interface utilisateur dépend de ce module (via `mobile_data_api.py`) pour récupérer :
    *   La liste des langues.
    *   La liste des pays.
    *   La liste des modèles de documents.
    *   La liste des produits (filtrée par langue).
*   **Module de Génération de Documents sur Mobile**: L'action de générer un PDF est déléguée à `LiteDocumentHandler` (qui fait partie conceptuellement du module de génération de documents).

## 6. Fichier Kivy Language (`mobile/mobile.kv`)

Le fichier `mobile/mobile.kv` existe mais contient actuellement des éléments placeholders et ne semble pas définir la structure de l'écran `DocumentGenerationScreen`, qui est entièrement construite en code Python dans `mobile/ui.py`. Il pourrait être utilisé à l'avenir pour styliser ou structurer des composants.
