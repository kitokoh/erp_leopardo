# Architecture Conceptuelle - Application Mobile

## 1. Introduction

Ce document décrit l'architecture conceptuelle de l'application mobile et ses interactions avec le système backend. L'application est conçue comme un client léger qui s'appuie sur un backend pour la logique métier principale, la persistance des données et certaines opérations gourmandes en ressources (comme la conversion PDF).

## 2. Vue d'Ensemble de l'Architecture

L'architecture peut être divisée en deux composants majeurs :

*   **L'Application Mobile Cliente**: Développée en Kivy (Python), elle tourne sur l'appareil de l'utilisateur.
*   **Le Système Backend (Application Principale)**: Fournit les données et services via une API RESTful.

```mermaid
graph LR
    subgraph Appareil Mobile
        A[Application Mobile Kivy] --> B{Interaction Utilisateur};
        B --> C[Interface Utilisateur (ui.py)];
        C --> D[Logique de Présentation/UI];
        D --> E[Module NLU (nlu_handler.py, nlu_controller.py)];
        D --> F[Gestionnaire de Documents Mobiles (document_handler.py)];
        F --> G[Logique de Génération de Document (local)];
        G --> H[Moteur de Template (Jinja2)];
        F --> I[Gestionnaire de Données (data_handler.py)];
        E --> I;
        I --> J[Communication API];
    end

    subgraph Serveur Backend
        K[API RESTful] --> L[Logique Métier & Services];
        L --> M[Base de Données Principale];
        L --> N[Service de Conversion PDF];
        L --> O[Gestion des Modèles de Documents];
    end

    J --> K;

    P[Plyer: Accès Fonctionnalités Natives]
    C --> P;
    F --> P;

    style A fill:#cde,stroke:#333,stroke-width:2px
    style K fill:#dec,stroke:#333,stroke-width:2px
```

## 3. Composants de l'Application Mobile Cliente

L'application mobile Kivy est structurée autour des composants/modules suivants :

*   **Interface Utilisateur (`mobile/ui.py`, `mobile/mobile.kv`)**:
    *   **Responsabilité**: Affichage des écrans, gestion des widgets Kivy, capture des entrées utilisateur (tactiles, texte).
    *   **Technologie**: Kivy.
    *   **Interaction**: Reçoit les actions de l'utilisateur et délègue le traitement à la logique de présentation ou aux handlers spécifiques. Affiche les données formatées. Interagit avec `Plyer` pour les fonctionnalités natives.

*   **Logique de Présentation/UI (intégrée dans `mobile/ui.py`)**:
    *   **Responsabilité**: Gérer l'état de l'interface utilisateur, orchestrer les appels aux modules de données ou de génération de documents en réponse aux actions de l'utilisateur, formater les données pour l'affichage.
    *   **Interaction**: S'interface avec le `Gestionnaire de Données` pour récupérer les informations à afficher et avec le `Gestionnaire de Documents Mobiles` pour initier la création de PDF.

*   **Module NLU (`mobile/nlu_handler.py`, `mobile/nlu_controller.py`)**:
    *   **Responsabilité**: Interpréter les commandes textuelles de l'utilisateur, en extraire les intentions et entités, et les traduire en actions compréhensibles par la logique de présentation.
    *   **Interaction**: Reçoit du texte de l'UI, le traite, et retourne une structure d'action à l'UI.

*   **Gestionnaire de Documents Mobiles (`mobile/document_handler.py` - `LiteDocumentHandler`)**:
    *   **Responsabilité**: Orchestrer le processus de génération de documents PDF. Prépare le contexte, gère le rendu des templates HTML (via Jinja2), et coordonne avec le `Gestionnaire de Données` pour la conversion HTML vers PDF via l'API.
    *   **Interaction**: Est appelé par la logique de présentation. Utilise le `Gestionnaire de Données` pour obtenir le contexte, le contenu des modèles, et pour la conversion PDF. Utilise `html_to_pdf_util` (Jinja2) pour le templating.

*   **Moteur de Template (Jinja2 via `html_to_pdf_util.py`)**:
    *   **Responsabilité**: Effectuer le rendu des modèles de documents HTML en y injectant les données du contexte.
    *   **Technologie**: Jinja2.
    *   **Interaction**: Utilisé par le `Gestionnaire de Documents Mobiles`.

*   **Gestionnaire de Données (`mobile/data_handler.py`)**:
    *   **Responsabilité**: Agir comme une couche d'abstraction pour toutes les communications avec l'API backend. Récupère les données (produits, clients, modèles, etc.) et relaie les requêtes (conversion PDF). Actuellement, il simule ces appels API.
    *   **Interaction**: Fournit des données et des services aux autres modules (UI, Gestionnaire de Documents). Effectue les "appels" à l'API backend.

*   **Plyer**:
    *   **Responsabilité**: Fournir un accès aux fonctionnalités natives de la plateforme mobile (partage de fichiers, client e-mail).
    *   **Technologie**: Plyer (bibliothèque Python).
    *   **Interaction**: Utilisé par l'UI et potentiellement par le `Gestionnaire de Documents Mobiles` (bien que l'appel à Plyer soit dans l'UI actuellement) pour les actions post-génération.

## 4. Système Backend (Application Principale)

Le backend est supposé fournir les services suivants via une API RESTful :

*   **API RESTful**: Point d'entrée pour toutes les requêtes de l'application mobile.
*   **Logique Métier & Services**: Contient la logique principale de l'application (gestion des clients, produits, commandes, règles de génération de documents, etc.).
*   **Base de Données Principale**: Stocke toutes les données de l'application (clients, produits, utilisateurs, modèles, documents générés, etc.).
*   **Service de Conversion PDF**: Un service capable de convertir du contenu HTML en un document PDF.
*   **Gestion des Modèles de Documents**: Stocke et sert les modèles de documents HTML.

## 5. Flux de Données et Interactions Clés

*   **Affichage Initial des Données**:
    1.  L'UI (ex: `DocumentGenerationScreen`) demande les listes initiales (langues, pays, modèles, produits) au `Gestionnaire de Données`.
    2.  Le `Gestionnaire de Données` simule des appels API au Backend.
    3.  Le Backend (simulé) retourne les données.
    4.  L'UI affiche les données dans les Spinners, listes, etc.

*   **Génération d'un PDF**:
    1.  L'UI collecte les sélections de l'utilisateur (langue, pays, produits, modèle, action PDF).
    2.  L'UI initie la génération via le `Gestionnaire de Documents Mobiles`.
    3.  Le `Gestionnaire de Documents Mobiles` demande le contexte documentaire et le contenu du modèle au `Gestionnaire de Données`.
    4.  Le `Gestionnaire de Données` simule les appels API pour obtenir ces informations du Backend.
    5.  Le `Gestionnaire de Documents Mobiles` utilise Jinja2 pour rendre le HTML.
    6.  Le HTML rendu est envoyé au `Gestionnaire de Données` pour conversion PDF.
    7.  Le `Gestionnaire de Données` simule un appel API au service de Conversion PDF du Backend.
    8.  Les octets du PDF sont retournés à l'UI.
    9.  L'UI sauvegarde le PDF temporairement et utilise `Plyer` pour le partage ou l'envoi par e-mail.

*   **Commande NLU**:
    1.  L'UI capture la commande textuelle.
    2.  Le texte est envoyé au `nlu_handler.py` pour analyse (intentions, entités).
    3.  Le résultat est envoyé au `nlu_controller.py` pour traduction en action UI.
    4.  L'UI exécute l'action (par exemple, met à jour un Spinner, appelle le `Gestionnaire de Documents Mobiles`).

## 6. Technologies Clés

*   **Application Mobile**:
    *   Python
    *   Kivy (pour l'UI)
    *   Plyer (pour l'accès aux fonctionnalités natives)
    *   Jinja2 (pour le templating HTML local avant envoi à l'API pour conversion PDF)
*   **Backend (Supposé)**:
    *   Technologie de serveur web (FastAPI est utilisé dans l'application desktop principale, donc potentiellement aussi pour l'API mobile).
    *   Base de données relationnelle ou NoSQL.
    *   Service de conversion HTML vers PDF (ex: WeasyPrint, wkhtmltopdf, ou un service cloud).
*   **Communication**:
    *   API RESTful (probablement JSON sur HTTPS).

Cette architecture vise la séparation des préoccupations, où l'application mobile gère la présentation et l'interaction utilisateur, tandis que le backend gère la logique métier lourde et la persistance des données.
