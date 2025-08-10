# Architecture Détaillée - Application Mobile

Ce document décrit l'architecture interne de l'application mobile compagnon du Client Document Manager. Pour une vue d'ensemble incluant l'application de bureau, veuillez consulter le document d'[Architecture Globale](./architecture_globale.md).

L'application mobile est développée en Python avec le framework Kivy et est conçue comme un client léger de l'API fournie par l'application de bureau.

## 1. Vue d'Ensemble de l'Architecture Mobile

```mermaid
graph TD
    A[Utilisateur Mobile] --> B[Interface Utilisateur (Kivy)];

    subgraph "Application Mobile (Kivy)"
        B -- Actions/Événements --> C{Logique de Présentation UI};
        C -- Appelle --> D[Gestionnaire de Données / Client API];
        C -- Appelle --> E[Gestionnaire de Documents Mobiles];
        C -- Appelle (optionnel) --> F[Module NLU (Traitement Langage Naturel)];

        E -- Utilise --> G[Moteur de Template (Jinja2)];
        E -- Demande conversion PDF --> D;
        F -- Retourne intention/entités --> C;

        D -- Requêtes HTTP --> H[API RESTful (Serveur FastAPI de l'App Desktop)];

        B -- Utilise --> I[Plyer (Accès Fonctionnalités Natives)];
        E -- Peut utiliser (via UI) --> I;
    end

    style B fill:#cde,stroke:#333,stroke-width:2px
    style H fill:#dec,stroke:#333,stroke-width:2px
    style I fill:#f9f,stroke:#333,stroke-width:1px
```

## 2. Composants Clés de l'Application Mobile

### 2.1. Interface Utilisateur (UI)

*   **Description**: Responsable de l'affichage des informations et de la capture des interactions utilisateur sur l'appareil mobile.
*   **Technologies**: Kivy (utilisant le langage `.kv` pour la structure et Python pour la logique).
*   **Composants Clés**:
    *   `mobile/main.py`: Point d'entrée de l'application Kivy.
    *   `mobile/mobile.kv`: Fichier principal définissant la structure des écrans (Screens) et des widgets Kivy.
    *   `mobile/ui.py`: Peut contenir des classes Python pour les widgets personnalisés, la logique de l'interface utilisateur et la gestion des écrans (ScreenManager).
*   **Responsabilités**:
    *   Présenter les données de manière adaptée aux écrans mobiles.
    *   Gérer la navigation entre les différents écrans.
    *   Capturer les entrées utilisateur (boutons, champs de texte, gestes).
    *   Déclencher des actions dans la Logique de Présentation UI.
    *   Utiliser `Plyer` pour accéder aux fonctionnalités natives (ex: partage de fichiers, e-mail).

### 2.2. Logique de Présentation UI

*   **Description**: Sert de pont entre l'interface utilisateur Kivy et les modules de service (Gestionnaire de Données, Gestionnaire de Documents).
*   **Composants Clés**: Souvent intégrée dans les classes Python associées aux écrans Kivy ou dans `mobile/ui.py`.
*   **Responsabilités**:
    *   Répondre aux événements de l'interface utilisateur (ex: clic sur un bouton).
    *   Préparer les données pour l'affichage dans les widgets Kivy.
    *   Orchestrer les appels aux gestionnaires appropriés (données, documents, NLU).
    *   Gérer l'état de l'interface utilisateur.

### 2.3. Gestionnaire de Données / Client API

*   **Description**: Encapsule toute la communication avec l'API RESTful du backend (l'application de bureau).
*   **Composants Clés**: `mobile/data_handler.py`.
*   **Responsabilités**:
    *   Effectuer des requêtes HTTP (GET, POST, etc.) vers l'API backend.
    *   Gérer l'authentification auprès de l'API (si applicable, ex: envoi de tokens).
    *   Récupérer les données du backend (listes de produits, clients, modèles, etc.).
    *   Envoyer des données au backend (ex: données pour la génération d'un document, demande de conversion PDF).
    *   Désérialiser les réponses JSON du backend en objets Python.
    *   Gérer les erreurs de communication réseau.
    *   *Note: La documentation existante indique que ce module simule actuellement les appels API. Une implémentation réelle nécessiterait une bibliothèque HTTP comme `requests` ou `httpx`.*

### 2.4. Gestionnaire de Documents Mobiles

*   **Description**: Orchestre le processus de génération de documents sur l'appareil mobile, en s'appuyant sur l'API backend pour les étapes gourmandes en ressources.
*   **Composants Clés**: `mobile/document_handler.py` (classe `LiteDocumentHandler`).
*   **Responsabilités**:
    *   Collecter les données nécessaires à la génération d'un document (provenant de l'UI et/ou via le Gestionnaire de Données).
    *   Récupérer les modèles de documents (probablement des modèles HTML via le Gestionnaire de Données).
    *   Utiliser un moteur de template (Jinja2) pour injecter les données dans le modèle HTML localement.
    *   Envoyer le HTML généré à l'API backend pour conversion en PDF (via le Gestionnaire de Données).
    *   Recevoir le fichier PDF du backend.
    *   Sauvegarder temporairement le PDF sur l'appareil.
    *   Coordonner avec l'UI pour permettre à l'utilisateur de visualiser, partager ou envoyer le PDF (potentiellement via `Plyer`).

### 2.5. Moteur de Template

*   **Description**: Utilisé pour le rendu local des modèles de documents (principalement HTML) avant leur éventuelle conversion en PDF par le backend.
*   **Technologie**: Jinja2 (utilisé via `html_to_pdf_util.py`, bien que ce dernier soit plus orienté backend, le principe de templating Jinja2 est applicable localement sur mobile).
*   **Responsabilités**:
    *   Prendre un modèle HTML et un contexte de données.
    *   Produire un document HTML rempli avec les données.

### 2.6. Module NLU (Traitement du Langage Naturel) - Optionnel/Basique

*   **Description**: Permet à l'utilisateur d'interagir avec l'application en utilisant des commandes textuelles simples.
*   **Composants Clés**:
    *   `mobile/nlu_handler.py`: Analyse le texte pour extraire des intentions et des entités.
    *   `mobile/nlu_controller.py`: Traduit les intentions/entités en actions concrètes dans l'UI.
*   **Responsabilités**:
    *   Interpréter des commandes utilisateur simples (basées sur des mots-clés et des règles prédéfinies).
    *   Faciliter certaines actions en évitant de naviguer dans plusieurs écrans.
    *   *Note: L'implémentation actuelle est décrite comme basique et basée sur des règles.*

### 2.7. Plyer

*   **Description**: Bibliothèque Python pour accéder aux fonctionnalités natives des plateformes mobiles (Android, iOS).
*   **Composants Clés**: Importation et utilisation des façades de Plyer (ex: `plyer.email`, `plyer.filechooser`, `plyer.sharing`).
*   **Responsabilités**:
    *   Permettre à l'application d'interagir avec d'autres applications ou fonctionnalités du système d'exploitation mobile (ex: ouvrir le client e-mail, partager un fichier).

## 3. Flux Typique (Exemple: Génération d'une Proforma PDF)

1.  **UI (Kivy)**: L'utilisateur navigue vers l'écran de génération de proforma, sélectionne un client, des produits, une langue, etc.
2.  **Logique de Présentation UI**: Récupère les sélections de l'utilisateur.
3.  **Gestionnaire de Données**: Si nécessaire, récupère des informations supplémentaires via l'API backend (ex: détails complets du client, prix des produits à jour).
4.  **Logique de Présentation UI**: Transmet les données collectées au `Gestionnaire de Documents Mobiles`.
5.  **Gestionnaire de Documents Mobiles**:
    a.  Demande le modèle HTML de la proforma (via le `Gestionnaire de Données` qui l'obtient de l'API backend).
    b.  Utilise Jinja2 pour injecter les données du client et des produits dans le modèle HTML, générant un document HTML.
    c.  Envoie ce HTML au `Gestionnaire de Données` avec une requête pour le convertir en PDF.
6.  **Gestionnaire de Données**: Envoie une requête POST à l'endpoint `/api/convert/html-to-pdf` (ou similaire) de l'API backend, avec le HTML en payload.
7.  **API Backend (Application Desktop)**: Reçoit le HTML, le convertit en PDF en utilisant ses propres outils (ex: WeasyPrint, ReportLab), et renvoie le fichier PDF binaire.
8.  **Gestionnaire de Données**: Reçoit la réponse PDF.
9.  **Gestionnaire de Documents Mobiles**: Sauvegarde le PDF dans un emplacement temporaire sur l'appareil.
10. **Logique de Présentation UI / UI (Kivy)**: Informe l'utilisateur que le document est prêt. Propose des options pour ouvrir, partager (via `Plyer.sharing.share_file()`) ou envoyer par e-mail (via `Plyer.email.send()`).

## 4. Communication avec le Backend

*   Toutes les interactions de données significatives et les opérations gourmandes en ressources (comme la conversion PDF) dépendent de l'API RESTful fournie par l'application de bureau.
*   La communication se fait via des requêtes HTTP/HTTPS.
*   Un mécanisme d'authentification (ex: tokens) est nécessaire pour sécuriser l'accès à l'API.

Cette architecture mobile vise à fournir une expérience utilisateur ciblée et efficace pour des tâches spécifiques, en tirant parti de la puissance et des données centralisées de l'application de bureau principale.
