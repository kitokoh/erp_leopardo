# Module : Génération de Documents sur Mobile

Ce document décrit le fonctionnement du module de génération de documents au sein de l'application mobile. Il se concentre sur la logique orchestrée par `LiteDocumentHandler` et ses interactions avec l'interface utilisateur et le système backend (via `mobile_data_api`).

## 1. Objectif Principal

L'objectif de ce module est de permettre la création de documents PDF basés sur des modèles prédéfinis et des données dynamiques (informations client, produits sélectionnés, etc.), directement depuis l'application mobile.

## 2. Composants Clés

*   **`LiteDocumentHandler` (dans `mobile/document_handler.py`)**: Classe principale responsable de la logique de génération de documents.
*   **`DocumentGenerationScreen` (dans `mobile/ui.py`)**: Interface utilisateur qui collecte les entrées de l'utilisateur (langue, pays, produits, modèle) et initie les actions de génération.
*   **`mobile_data_api.py` (dans `mobile/data_handler.py`)**: Couche d'abstraction pour la communication avec l'API backend, fournissant les données et les services nécessaires (ex: conversion HTML vers PDF).
*   **`html_to_pdf_util.py` (utilitaire partagé)**: Utilisé pour le rendu des modèles HTML avec le moteur de template Jinja2.

## 3. Processus de Génération de Documents

Le processus typique de génération d'un document est le suivant :

1.  **Collecte des Données d'Entrée (via `DocumentGenerationScreen`)**:
    *   Langue sélectionnée.
    *   Pays sélectionné.
    *   Produits sélectionnés avec leurs quantités.
    *   Modèle de document sélectionné.
    *   Action PDF souhaitée ("separate" pour des PDF distincts par produit/template, ou "combine" pour un seul PDF).

2.  **Préparation du Contexte du Document (`LiteDocumentHandler._prepare_document_context`)**:
    *   Récupération des identifiants du client par défaut et de l'entreprise via `mobile_data_api.get_client_and_company_ids_from_api()`.
    *   Construction d'un contexte enrichi en appelant `mobile_data_api.get_document_context_data_from_api()`. Ce contexte inclut les détails du client, de l'entreprise, les informations sur les produits sélectionnés, la date, etc.
    *   Le pays sélectionné est ajouté au contexte.

3.  **Génération des Sorties PDF (`LiteDocumentHandler._generate_pdf_outputs`)**:
    *   Pour chaque modèle de document spécifié (actuellement, un seul modèle est sélectionné via l'UI) :
        *   **Récupération du Contenu du Modèle**:
            *   Si des données brutes de modèle sont fournies directement (peu probable dans le flux UI actuel), elles sont utilisées.
            *   Sinon, le contenu du modèle HTML est récupéré via `mobile_data_api.get_template_content_from_api()` en utilisant l'ID du modèle.
        *   **Rendu HTML**: Le contenu du modèle HTML est rendu en utilisant `html_to_pdf_util.render_html_template()` avec le contexte documentaire préparé à l'étape précédente. Cette étape utilise Jinja2 pour insérer les données dynamiques dans le HTML.
        *   **Conversion HTML vers PDF**:
            *   Si l'action est "separate", le HTML rendu est envoyé à `mobile_data_api.convert_html_to_pdf_api()` pour obtenir les octets du PDF. Chaque PDF généré est stocké avec son nom.
            *   Si l'action est "combine", tous les HTML rendus sont concaténés (avec des sauts de page HTML entre eux). Le HTML combiné est ensuite envoyé à `mobile_data_api.convert_html_to_pdf_api()` pour produire un unique PDF.
    *   La méthode retourne une liste de tuples `(nom_document, octets_pdf)`.

4.  **Gestion des Fichiers PDF (dans `DocumentGenerationScreen` et `LiteDocumentHandler`)**:
    *   Les octets PDF retournés sont sauvegardés dans des fichiers temporaires sur l'appareil.
        *   `LiteDocumentHandler.generate_and_visualize_pdfs` sauvegarde les fichiers dans un répertoire temporaire (obtenu via `mobile_data_api.get_mobile_temp_dir()`).
        *   `DocumentGenerationScreen.on_generate_pdf_button_pressed` et `on_email_pdf_button_pressed` utilisent `tempfile.NamedTemporaryFile` ou `tempfile.mkstemp` pour créer des fichiers PDF temporaires.
    *   Ces fichiers temporaires sont suivis dans `DocumentGenerationScreen.app_temporary_files` et peuvent être supprimés via le bouton "Clear Temporary Files".

5.  **Actions Post-Génération (dans `DocumentGenerationScreen`)**:
    *   **Prévisualisation/Partage**: `plyer.sharing.share_file()` est utilisé pour tenter d'ouvrir ou de partager le fichier PDF généré avec d'autres applications.
    *   **Envoi par E-mail**: `plyer.email.send()` est utilisé pour ouvrir l'application e-mail par défaut avec le(s) PDF(s) en pièce jointe.

## 4. Types de Documents Supportés

Les types de documents supportés dépendent des modèles de documents configurés dans le système backend et accessibles via `mobile_data_api.get_document_templates_from_api()`. L'application mobile sélectionne un de ces modèles pour la génération.

## 5. Dépendances Clés

*   **API Backend**: Le module dépend fortement de l'API backend pour :
    *   Fournir les données de base (clients, entreprise, produits, modèles).
    *   Fournir le contexte documentaire complet.
    *   Effectuer la conversion HTML vers PDF.
*   **`html_to_pdf_util`**: Pour le rendu des templates HTML avec Jinja2.
*   **Plyer**: Pour les fonctionnalités de partage de fichiers et d'envoi d'e-mails natifs.

## 6. Points d'Attention et Limitations Actuelles

*   **Conversion PDF Externalisée**: La conversion effective de HTML en PDF n'est pas réalisée localement sur l'appareil mobile mais est déléguée à une API (`mobile_data_api.convert_html_to_pdf_api()`). Cela nécessite une connectivité réseau au moment de la génération.
*   **Gestion des Modèles**: Les modèles de documents sont gérés côté backend. L'application mobile récupère la liste des modèles et leur contenu via l'API.
*   **Gestion des Erreurs**: Des mécanismes de base pour la gestion des erreurs (par exemple, échec de la récupération du contexte, échec de la génération du PDF) sont présents, avec des messages affichés à l'utilisateur via des popups.
*   **Répertoires Temporaires**: La gestion des répertoires temporaires pour les PDF générés est gérée via `mobile_data_api.get_mobile_temp_dir()` et `tempfile`.
