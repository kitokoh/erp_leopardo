# Architecture Globale

Ce document décrit l'architecture globale du système Client Document Manager, qui se compose de deux éléments principaux : une application de bureau complète et une application mobile compagnon.

## 1. Vue d'Ensemble

Le système est conçu autour d'une application de bureau centrale qui gère la majorité de la logique métier, la persistance des données et expose une API. L'application mobile agit comme un client de cette API pour des fonctionnalités spécifiques en situation de mobilité.

```mermaid
graph TD
    subgraph "Système Client Document Manager"
        AppDesktop[Application Desktop (PyQt5, Python)]
        AppMobile[Application Mobile (Kivy, Python)]
    end

    APIServer[API RESTful (FastAPI, intégrée à AppDesktop)]

    AppDesktop --> DB[(Base de Données SQLite)]
    AppDesktop -- Expose --> APIServer
    AppMobile -- Consomme --> APIServer

    UtilisateurDesktop[Utilisateur Desktop] --> AppDesktop
    UtilisateurMobile[Utilisateur Mobile] --> AppMobile

    style AppDesktop fill:#add,stroke:#333,stroke-width:2px
    style AppMobile fill:#dda,stroke:#333,stroke-width:2px
    style APIServer fill:#dad,stroke:#333,stroke-width:2px
    style DB fill:#ddd,stroke:#333,stroke-width:2px
```

## 2. Composants Principaux

### 2.1. Application Desktop

*   **Description**: Application principale et la plus complète du système. Elle est développée en Python avec la bibliothèque PyQt5 pour l'interface utilisateur.
*   **Responsabilités Clés**:
    *   Gestion complète des données (clients, produits, projets, documents, utilisateurs, etc.).
    *   Fourniture de l'interface utilisateur principale pour toutes les fonctionnalités.
    *   Logique métier pour toutes les opérations.
    *   Génération de documents (PDF, DOCX).
    *   Hébergement de la base de données (SQLite par défaut).
    *   Exposition d'une API RESTful via un serveur FastAPI intégré pour permettre l'accès à certaines fonctionnalités et données par des clients externes (comme l'application mobile).
*   **Technologies Principales**: Python, PyQt5, SQLAlchemy, FastAPI.
*   **Détails**: Voir [Architecture Desktop](./architecture_desktop.md).

### 2.2. Application Mobile

*   **Description**: Application compagnon conçue pour offrir un accès mobile à des fonctionnalités clés. Elle est développée en Python avec le framework Kivy.
*   **Responsabilités Clés**:
    *   Fournir une interface utilisateur optimisée pour les appareils mobiles.
    *   Permettre la consultation de données (ex: fiches produits, informations clients).
    *   Permettre la génération rapide de certains types de documents (ex: proformas).
    *   Interagir avec l'API de l'application de bureau pour récupérer des données et déclencher des actions (ex: conversion de documents HTML en PDF).
    *   Peut inclure des fonctionnalités spécifiques comme l'interaction en langage naturel (NLU) pour simplifier les commandes.
*   **Technologies Principales**: Python, Kivy, Jinja2 (pour le templating local).
*   **Détails**: Voir [Architecture Mobile](./architecture_mobile.md).

### 2.3. API RESTful (Serveur FastAPI)

*   **Description**: Intégrée à l'application de bureau, cette API sert de pont entre l'application de bureau (agissant comme serveur) et les clients externes comme l'application mobile.
*   **Responsabilités Clés**:
    *   Exposer de manière sécurisée des points d'accès (endpoints) pour lire et potentiellement écrire des données.
    *   Fournir des services tels que la conversion de documents (ex: HTML vers PDF).
    *   Gérer l'authentification et l'autorisation pour les requêtes API.
*   **Technologies Principales**: FastAPI, Python.
*   **Détails**: Voir [Spécifications API](./api_specifications.md).

### 2.4. Base de Données

*   **Description**: Système de persistance central utilisé par l'application de bureau.
*   **Responsabilités Clés**:
    *   Stocker toutes les données de l'application (clients, produits, utilisateurs, documents générés, paramètres, etc.).
    *   Assurer l'intégrité et la cohérence des données.
*   **Technologies Principales**: SQLite (par défaut), SQLAlchemy (ORM).
*   **Détails**: Voir [Schéma de la Base de Données](./schema_base_de_donnees.md).

## 3. Flux d'Interaction Majeurs

### 3.1. Flux de Données Standard (Application Desktop)

1.  L'utilisateur interagit avec l'interface PyQt5.
2.  Les actions sont traitées par la logique de présentation et la logique métier.
3.  La logique métier interagit avec la couche d'accès aux données (CRUDs SQLAlchemy).
4.  Les données sont lues/écrites dans la base de données SQLite.
5.  Les résultats sont renvoyés à l'interface utilisateur.

### 3.2. Flux de Données pour l'Application Mobile (Ex: Génération d'un Document)

1.  L'utilisateur mobile interagit avec l'interface Kivy pour sélectionner des options (ex: client, produits pour une proforma).
2.  L'application mobile collecte les informations et prépare une requête.
3.  Elle peut utiliser un moteur de template local (Jinja2) pour générer un contenu intermédiaire (ex: HTML).
4.  L'application mobile envoie une requête à l'API RESTful de l'application de bureau (ex: pour obtenir des données à jour ou pour demander la conversion du HTML en PDF).
5.  Le serveur FastAPI de l'application de bureau reçoit la requête.
6.  La logique métier de l'application de bureau traite la requête (ex: récupère les données de la base de données, effectue la conversion PDF).
7.  L'API renvoie la réponse (ex: données JSON, fichier PDF) à l'application mobile.
8.  L'application mobile affiche le résultat à l'utilisateur ou permet le partage du document.

## 4. Considérations Architecturales Clés

*   **Couplage Lâche via API**: L'application mobile est découplée de l'application de bureau grâce à l'API. Cela permet des développements et des déploiements plus indépendants.
*   **Centralisation de la Logique Métier**: La logique métier principale réside dans l'application de bureau, ce qui assure la cohérence. L'API expose cette logique de manière contrôlée.
*   **Dépendance de l'Application Mobile**: L'application mobile dépend de la disponibilité et de la connectivité à l'API de l'application de bureau pour la plupart de ses fonctionnalités.
*   **Sécurité de l'API**: Des mécanismes d'authentification et d'autorisation robustes sont nécessaires pour protéger l'API.

Cette architecture globale permet de combiner la richesse fonctionnelle d'une application de bureau avec la flexibilité d'un accès mobile pour des tâches spécifiques.
Les diagrammes illustrant ces interactions sont disponibles dans le dossier [`diagrammes/`](./diagrammes/).
