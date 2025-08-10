# Documentation de Conception - Client Document Manager

Bienvenue dans la documentation de conception du projet Client Document Manager. Ce dossier contient un ensemble de documents visant à expliquer en détail l'architecture, les fonctionnalités et les aspects techniques de l'application.

## Organisation des Documents

La conception est structurée de la manière suivante :

*   **[`architecture_globale.md`](./architecture_globale.md)**: Décrit la vue d'ensemble de l'architecture, incluant les interactions entre l'application de bureau principale et l'application mobile compagnon.
*   **[`architecture_desktop.md`](./architecture_desktop.md)**: Fournit une description détaillée de l'architecture interne de l'application de bureau (PyQt5).
*   **[`architecture_mobile.md`](./architecture_mobile.md)**: Fournit une description détaillée de l'architecture interne de l'application mobile (Kivy).
*   **[`diagrammes/`](./diagrammes/)**: Contient les diagrammes visuels illustrant l'architecture et les flux.
    *   Consultez le [`README.md`](./diagrammes/README.md) dans ce dossier pour plus d'informations sur les diagrammes.
*   **[`api_specifications.md`](./api_specifications.md)**: Spécifie les points d'accès (endpoints) de l'API RESTful fournie par le serveur FastAPI intégré à l'application de bureau.
*   **[`schema_base_de_donnees.md`](./schema_base_de_donnees.md)**: Détaille la structure de la base de données (SQLite via SQLAlchemy), incluant les tables principales, leurs colonnes et leurs relations.
*   **[`interfaces_utilisateur.md`](./interfaces_utilisateur.md)**: Présente les aspects clés des interfaces utilisateur pour l'application de bureau et mobile, ainsi que les principaux flux de navigation.
*   **[`fonctionnalites_cles.md`](./fonctionnalites_cles.md)**: Décrit en détail les fonctionnalités majeures offertes par l'application.
*   **[`technologies.md`](./technologies.md)**: Liste les technologies, frameworks, bibliothèques et outils utilisés dans le projet, avec une justification de leur choix.
*   **[`guide_deploiement_maintenance.md`](./guide_deploiement_maintenance.md)**: Fournit des instructions et des considérations pour le déploiement et la maintenance de l'application.
*   **[`strategie_tests.md`](./strategie_tests.md)**: Décrit l'approche et la stratégie adoptées pour les tests et la validation de l'application.

Ces documents sont basés sur l'analyse du code existant et de la documentation présente dans le dossier `cahier/`. L'objectif est de fournir une source d'information centralisée et claire pour comprendre la conception actuelle du projet.
