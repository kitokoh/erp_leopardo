# Technologies Utilisées

Ce document liste les principales technologies, frameworks, bibliothèques et outils utilisés dans le développement de l'application Client Document Manager (versions desktop et mobile), ainsi qu'une brève justification de leur choix lorsque cela est pertinent.

## 1. Langage de Programmation Principal

*   **Python (3.x)**
    *   **Description**: Langage de programmation principal pour l'ensemble du projet (desktop, mobile, API).
    *   **Justification**:
        *   Lisibilité et syntaxe claire, facilitant le développement et la maintenance.
        *   Vaste écosystème de bibliothèques tierces pour de nombreuses fonctionnalités (GUI, web, manipulation de données, etc.).
        *   Multiplateforme (Windows, macOS, Linux).
        *   Courbe d'apprentissage relativement douce.
        *   Adapté aussi bien pour le scripting que pour le développement d'applications complexes.

## 2. Application Desktop

*   **PyQt5**
    *   **Description**: Binding Python pour le framework Qt, utilisé pour la création de l'interface utilisateur graphique (GUI).
    *   **Justification**:
        *   Fournit un ensemble riche et mature de widgets UI.
        *   Bonnes performances et apparence native sur différentes plateformes.
        *   Mécanisme de signaux et slots pour une communication événementielle robuste.
        *   Qt Designer pour la conception visuelle des interfaces (fichiers `.ui`).
    *   **Alternatives considérées (implicitement)**: Tkinter (plus simple, moins de fonctionnalités), Kivy (utilisé pour le mobile, mais PyQt est souvent préféré pour les applications desktop complexes), wxPython.

*   **SQLAlchemy**
    *   **Description**: ORM (Object-Relational Mapper) Python qui fournit une manière de haut niveau d'interagir avec les bases de données relationnelles.
    *   **Justification**:
        *   Abstrait les différences entre les SGBD, facilitant la portabilité (bien que SQLite soit le défaut).
        *   Permet de travailler avec la base de données en utilisant des objets Python plutôt que du SQL brut.
        *   Gestion des sessions, transactions, et migrations (avec Alembic, non confirmé mais typique).
        *   Réduit le code répétitif pour les opérations CRUD.

*   **SQLite**
    *   **Description**: Moteur de base de données relationnelle sans serveur, basé sur des fichiers. Utilisé comme base de données par défaut.
    *   **Justification**:
        *   Léger, facile à intégrer et à déployer (pas de serveur séparé à gérer).
        *   Adapté pour les applications desktop autonomes ou de petite à moyenne taille.
        *   Bonnes performances pour la plupart des cas d'usage de l'application.

*   **FastAPI**
    *   **Description**: Framework web Python moderne et performant pour la création d'API RESTful. Utilisé pour le serveur API intégré.
    *   **Justification**:
        *   Haute performance (basé sur Starlette et Pydantic).
        *   Validation automatique des données des requêtes et réponses grâce à Pydantic et aux type hints Python.
        *   Génération automatique de documentation interactive de l'API (Swagger UI, ReDoc).
        *   Syntaxe intuitive et développement rapide.

*   **Uvicorn**
    *   **Description**: Serveur ASGI (Asynchronous Server Gateway Interface) utilisé pour exécuter l'application FastAPI.
    *   **Justification**: Serveur haute performance recommandé pour FastAPI.

*   **openpyxl**
    *   **Description**: Bibliothèque Python pour lire et écrire des fichiers Excel 2010+ (`.xlsx`/`.xlsm`).
    *   **Justification**: Essentiel pour la manipulation des modèles Excel et la génération de documents basés sur Excel.

*   **python-docx**
    *   **Description**: Bibliothèque Python pour créer et mettre à jour des fichiers Microsoft Word (`.docx`).
    *   **Justification**: Utilisé pour remplir les modèles Word avec des données dynamiques.

*   **ReportLab**
    *   **Description**: Bibliothèque Python pour créer des documents PDF par programmation.
    *   **Justification**: Utilisé pour la génération de PDF, notamment les pages de garde et potentiellement la compilation de PDF. (Peut aussi être utilisé indirectement si une conversion HTML->PDF s'appuie sur un outil qui l'utilise).

*   **Jinja2**
    *   **Description**: Moteur de template Python moderne et populaire.
    *   **Justification**: Utilisé pour le templating HTML (par exemple, avant conversion en PDF) et potentiellement pour d'autres types de modèles de texte.

*   **Pandas**
    *   **Description**: Bibliothèque puissante pour la manipulation et l'analyse de données.
    *   **Justification**: Mentionné dans le `README.md` comme utilisé pour la création initiale de modèles par défaut. Peut être utilisé pour des tâches d'import/export de données ou d'analyse si nécessaire.

*   **QSS (Qt Style Sheets)**
    *   **Description**: Mécanisme de Qt pour personnaliser l'apparence des applications Qt en utilisant une syntaxe similaire à CSS.
    *   **Justification**: Permet de créer une interface utilisateur visuellement cohérente et personnalisée (voir `style.qss`).

*   **Internationalisation (Qt Linguist, fichiers `.ts`, `.qm`)**
    *   **Description**: Outils et formats de Qt pour la traduction de l'interface utilisateur.
    *   **Justification**: Permet de supporter plusieurs langues dans l'application desktop.

## 3. Application Mobile

*   **Kivy**
    *   **Description**: Framework Python open-source pour le développement d'applications multi-touch avec des interfaces utilisateur naturelles (NUI).
    *   **Justification**:
        *   Permet de développer des applications mobiles multiplateformes (Android, iOS, Windows, macOS, Linux) avec une seule base de code Python.
        *   Bon support pour les graphismes et les interactions tactiles.
        *   Utilise son propre langage (`.kv`) pour la conception de l'interface, séparant la logique de la présentation.

*   **Plyer**
    *   **Description**: Bibliothèque Python qui fournit un accès aux fonctionnalités matérielles et natives des plateformes mobiles (et desktop).
    *   **Justification**: Essentiel pour que l'application mobile puisse interagir avec le système d'exploitation sous-jacent (ex: partage de fichiers, envoi d'e-mails via le client natif, accès à la caméra/GPS si nécessaire).

*   **Jinja2** (comme pour le desktop)
    *   **Description**: Utilisé pour le templating HTML local sur l'appareil mobile avant d'envoyer le HTML à l'API backend pour conversion en PDF.

*   **Requests / httpx (Supposé)**
    *   **Description**: Bibliothèques Python pour effectuer des requêtes HTTP.
    *   **Justification**: Nécessaire pour que l'application mobile communique avec l'API RESTful du backend. `data_handler.py` simule actuellement cela, mais une implémentation réelle utiliserait l'une de ces bibliothèques.

## 4. Outils de Développement et de Gestion de Projet

*   **Git**
    *   **Description**: Système de contrôle de version distribué.
    *   **Justification**: Standard de l'industrie pour le suivi des modifications du code, la collaboration et la gestion des branches.

*   **Virtualenv / venv**
    *   **Description**: Outil pour créer des environnements Python isolés.
    *   **Justification**: Permet de gérer les dépendances spécifiques au projet sans conflits avec d'autres projets ou l'installation Python globale.

*   **pip**
    *   **Description**: Gestionnaire de paquets Python.
    *   **Justification**: Utilisé pour installer et gérer les bibliothèques Python à partir de PyPI (Python Package Index) via `requirements.txt`.

*   **PyInstaller (Potentiel)**
    *   **Description**: Outil pour empaqueter des applications Python en exécutables autonomes.
    *   **Justification**: La présence d'un fichier `main.spec` suggère son utilisation pour créer une version distribuable de l'application desktop.

*   **pytest (Potentiel, pour les tests)**
    *   **Description**: Framework de test Python populaire.
    *   **Justification**: Le dossier `tests/` et les noms de fichiers suggèrent l'utilisation de pytest ou d'un framework similaire (comme `unittest` de la bibliothèque standard) pour les tests unitaires et d'intégration.

## 5. Intégrations Spécifiques

*   **API Google People**: Pour la synchronisation des contacts.
*   **API WooCommerce**: Pour l'intégration e-commerce.
*   **API Botpress**: Pour l'intégration avec la plateforme de chatbot.
*   **API WhatsApp (non officielle ou via un service tiers)**: Pour les fonctionnalités liées à WhatsApp.

Cette liste reflète les technologies clés identifiées. Le choix de ces technologies semble cohérent avec les objectifs du projet, privilégiant l'écosystème Python pour une base de code unifiée et tirant parti de bibliothèques matures pour des fonctionnalités spécifiques.
