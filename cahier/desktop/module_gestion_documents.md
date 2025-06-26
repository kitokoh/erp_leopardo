# Module : Gestion des Documents (Desktop)

## 1. Objectif Principal

Le module de Gestion des Documents est au cœur de l'application ClientDocManager. Son objectif principal est de permettre aux utilisateurs de créer, gérer, organiser, et générer une variété de documents commerciaux et administratifs de manière efficace et centralisée. Il vise à standardiser la production documentaire et à faciliter l'accès et le suivi des documents importants.

## 2. Composants Clés et Fonctionnalités

*   **Fenêtre Principale (`DocumentManager` dans `main_window.py`)**:
    *   Sert de point d'entrée principal après la connexion de l'utilisateur.
    *   Fournit la structure de navigation globale (menu, barre d'outils, volets) pour accéder aux différentes fonctionnalités, y compris celles liées aux documents.
    *   Affiche potentiellement des listes de documents récents, des tableaux de bord liés aux documents, ou des vues permettant de parcourir les documents existants.
    *   Contient les actions pour initier la création de nouveaux documents.

*   **Génération de Documents (`document_generator/`)**:
    *   **`html_generator.py`**: Contient la logique pour générer des documents au format HTML à partir de modèles (probablement Jinja2) et de données contextuelles.
    *   **`docx_generator.py`**: Contient la logique pour générer des documents au format DOCX (Microsoft Word) en utilisant la bibliothèque `python-docx`.
    *   **`cover_page_generator.py`**: Spécifiquement pour la génération de pages de garde.
    *   **`context_builder.py`**: Responsable de la collecte et de la structuration des données (contexte) nécessaires pour remplir les modèles de documents. Ce contexte peut inclure des informations sur le client, l'entreprise, les produits, les conditions commerciales, etc.
    *   **Utilisation de Modèles**: Le système s'appuie sur des fichiers de modèles (par exemple, `.docx`, `.html`) qui définissent la structure et les champs variables des documents. Ces modèles sont stockés dans le dossier `templates/` (organisé par langue).

*   **Conversion HTML vers PDF (`html_to_pdf_util.py`)**:
    *   Fournit des utilitaires pour convertir le contenu HTML (généré par `html_generator.py` ou autre) en documents PDF. Cela implique généralement une bibliothèque ou un outil externe (ex: WeasyPrint, ReportLab, ou un appel à une API si la conversion est externalisée).

*   **Dialogues Spécifiques aux Documents**:
    *   **`dialogs/create_document_dialog.py`**: Interface utilisateur permettant de sélectionner le type de document à créer, de choisir un client, d'ajouter des produits, de spécifier des conditions, etc., avant la génération.
    *   **`dialogs/compile_pdf_dialog.py`**: Potentiellement pour assembler plusieurs documents en un seul PDF ou pour des options de compilation avancées.
    *   **`dialogs/select_client_attachment_dialog.py`**, **`dialogs/select_utility_attachment_dialog.py`**: Pour sélectionner et gérer les pièces jointes aux documents ou aux entités liées.
    *   **`project_management/dialogs/cover_page_editor_dialog.py`**: Éditeur spécifique pour les pages de garde dans le contexte de la gestion de projet.

*   **Types de Documents Gérés (Exemples basés sur les modèles et la structure)**:
    *   Factures Proforma (`proforma_invoice_template.html`, `proforma_template.xlsx`)
    *   Factures Finales (logique dans `invoicing/`)
    *   Contrats de Vente (`sales_contract_template.html`, `contrat_vente_template.xlsx`)
    *   Spécifications Techniques (`technical_specifications_template.html`, `specification_technique_template.xlsx`)
    *   Packing Lists (`packing_list_template.html`, `packing_liste_template.xlsx`)
    *   Images Produits (document listant des images produits - `product_images_template.html`)
    *   Documents de Garantie (`warranty_document_template.html`)
    *   Pages de Contact (`contact_page_template.html`)
    *   Pages de Garde

*   **Stockage et Organisation**:
    *   Les documents générés sont susceptibles d'être stockés dans des emplacements spécifiques (par exemple, liés aux clients, aux projets).
    *   La base de données (`db/models/documents.py`, `db/models/project_files.py`, etc.) contient les métadonnées des documents (nom, type, date, chemin d'accès, liens vers d'autres entités).

*   **Fonctionnalités Associées**:
    *   Recherche et filtrage de documents.
    *   Prévisualisation des documents.
    *   Envoi de documents par e-mail (via `email_service.py`).
    *   Gestion des versions (moins probable dans la structure actuelle, mais une considération).
    *   Archivage de documents.

## 3. Flux de Travail Typique (Exemple : Création d'une Facture Proforma)

1.  **Initiation**: L'utilisateur, depuis `DocumentManager`, choisit de créer une nouvelle facture proforma.
2.  **Ouverture du Dialogue**: `CreateDocumentDialog` (ou un dialogue similaire) s'ouvre.
3.  **Sélection des Données**:
    *   L'utilisateur sélectionne un client.
    *   L'utilisateur ajoute des produits/services à la proforma, spécifiant les quantités et les prix (qui peuvent être récupérés de la base de données).
    *   L'utilisateur peut spécifier des conditions particulières, des dates, etc.
4.  **Validation et Collecte du Contexte**:
    *   Le dialogue valide les entrées.
    *   `document_generator/context_builder.py` est sollicité pour assembler toutes les données nécessaires (informations client, détails de l'entreprise de l'utilisateur, liste des produits, totaux, taxes, etc.) dans un dictionnaire de contexte.
5.  **Génération du Document**:
    *   La logique de génération (par exemple, dans `html_generator.py` ou une fonction dédiée) prend le contexte et le modèle HTML de la facture proforma.
    *   Le moteur de template (Jinja2) remplit le modèle avec les données du contexte, produisant un fichier HTML.
6.  **Conversion en PDF (si applicable)**:
    *   Le fichier HTML est passé à `html_to_pdf_util.py` pour être converti en PDF.
7.  **Sauvegarde et Affichage**:
    *   Le PDF généré est sauvegardé à un emplacement approprié.
    *   Les métadonnées du document sont enregistrées en base de données (via un CRUD spécifique, par exemple `proforma_invoices_crud.py`).
    *   Le document peut être automatiquement ouvert pour prévisualisation ou l'utilisateur peut être notifié de sa création.
8.  **Actions Postérieures**: L'utilisateur peut ensuite choisir d'envoyer la proforma par e-mail, de l'imprimer, etc.

## 4. Interactions avec d'Autres Modules

*   **Authentification et Gestion des Utilisateurs**: Détermine qui peut créer/modifier/visualiser certains types de documents en fonction des rôles et permissions. Les informations de l'utilisateur peuvent apparaître sur les documents (ex: "créé par").
*   **Gestion des Clients**: Fournit les informations client (nom, adresse, contact) pour les documents. Les documents sont souvent liés à des clients spécifiques.
*   **Gestion des Produits**: Fournit les descriptions, prix, et autres détails des produits/services listés dans les documents.
*   **Facturation et Paiements**: La génération de factures finales est une extension de ce module. Les proformas peuvent être converties en factures.
*   **Gestion de Projet**: Les documents peuvent être liés à des projets spécifiques (plans, rapports, contrats).
*   **Paramètres et Configuration**: Les modèles de documents, les informations de l'entreprise de l'utilisateur (logo, adresse pour les en-têtes) sont configurés ici.
*   **Gestion des E-mails**: Utilisé pour envoyer les documents générés aux clients ou autres destinataires.
*   **Base de Données**: Tous les métadonnées des documents et les liens vers les fichiers sont stockés et gérés via la couche d'accès aux données.

## 5. Points d'Attention

*   **Gestion des Modèles**: La flexibilité et la facilité de modification des modèles de documents sont cruciales.
*   **Performance de Génération**: Pour les documents complexes ou volumineux, la performance du processus de génération et de conversion PDF est importante.
*   **Cohérence des Données**: Assurer que les données utilisées pour générer les documents (prix des produits, adresses clients) sont à jour et exactes.
*   **Sécurité d'Accès**: Contrôler qui peut accéder à quels documents.
