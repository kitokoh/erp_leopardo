# Guide de Déploiement et de Maintenance

Ce document fournit des directives et des considérations pour le déploiement et la maintenance de l'application Client Document Manager (versions desktop et mobile) ainsi que du serveur API associé.

## 1. Déploiement de l'Application Desktop

### 1.1. Prérequis

*   **Python**: Une version compatible de Python (3.7+ recommandé) doit être installée sur la machine cible.
*   **Dépendances**: Toutes les dépendances listées dans `requirements.txt` doivent être installées. Idéalement, utiliser un environnement virtuel.
*   **Polices**: Les polices personnalisées (fichiers `.ttf` dans le dossier `fonts/`) doivent être présentes pour un rendu correct des PDF (notamment les pages de garde).
*   **Système d'Exploitation**: L'application est développée en Python/PyQt5 et devrait être compatible avec Windows, macOS et Linux. Des tests spécifiques sur chaque plateforme sont nécessaires.

### 1.2. Options de Déploiement

**Option 1: Exécution à partir des Sources (pour développeurs ou utilisateurs avancés)**

1.  Cloner le dépôt Git (si applicable) ou copier les fichiers sources.
2.  Créer et activer un environnement virtuel :
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```
3.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
4.  Exécuter l'application :
    ```bash
    python main.py
    ```

**Option 2: Création d'un Exécutable Autonome (Recommandé pour les utilisateurs finaux)**

*   Utiliser un outil comme **PyInstaller** (la présence d'un fichier `main.spec` le suggère).
*   **Processus Général avec PyInstaller**:
    1.  Installer PyInstaller: `pip install pyinstaller`.
    2.  Naviguer vers le répertoire racine du projet.
    3.  Exécuter PyInstaller avec le fichier de spécification (`main.spec`) ou directement sur le script principal :
        ```bash
        pyinstaller main.spec
        # OU
        pyinstaller --name ClientDocManager --windowed --onefile main.py \
                    --add-data "templates:templates" \
                    --add-data "fonts:fonts" \
                    --add-data "icons:icons" \
                    --add-data "translations:translations" \
                    --add-data "email_template_designs:email_template_designs" \
                    # ... (ajouter d'autres ressources nécessaires comme .ui, .qrc, images)
        ```
        *   `--windowed`: Pour les applications GUI (pas de console).
        *   `--onefile`: Crée un seul exécutable (peut être plus lent au démarrage). Omettre pour un dossier de distribution.
        *   `--add-data`: Pour inclure des dossiers/fichiers non-code (modèles, polices, icônes, traductions). Le format est `SOURCE:DESTINATION_IN_BUNDLE`.
        *   Il est crucial d'inclure toutes les ressources nécessaires (icônes, modèles, polices, fichiers de traduction `.qm`, etc.). Le fichier `main.spec` permet une configuration plus fine.
    4.  L'exécutable sera créé dans le sous-dossier `dist/`.
*   **Distribution**: Distribuer le contenu du dossier `dist/` (ou le fichier unique si `--onefile` est utilisé). Un installateur (ex: Inno Setup pour Windows, `main.iss` est présent) peut être créé pour faciliter l'installation.

### 1.3. Configuration Initiale

*   **Base de Données**: Au premier lancement, l'application créera la base de données SQLite (`client_manager_app.db`) si elle n'existe pas, et exécutera le seeding de données initiales.
*   **Informations de l'Entreprise**: L'utilisateur devra probablement configurer les informations de sa propre entreprise (nom, logo, adresse) via l'interface des paramètres.
*   **Paramètres SMTP**: Pour l'envoi d'e-mails, les paramètres du serveur SMTP devront être configurés.
*   **Chemins des Dossiers**: Vérifier et ajuster si nécessaire les chemins par défaut pour les modèles et les fichiers clients.

## 2. Déploiement de l'Application Mobile (Kivy)

### 2.1. Prérequis

*   Dépend des plateformes cibles (Android, iOS).
*   Outils de build spécifiques à chaque plateforme (Android SDK/NDK, Xcode).

### 2.2. Processus de Packaging

*   Utiliser des outils comme **Buildozer** ou **pyinstaller-android** (pour Android) / **Kivy-iOS** (pour iOS) pour empaqueter l'application Kivy en un format distribuable (`.apk` pour Android, `.ipa` pour iOS).
*   **Configuration de Buildozer (`buildozer.spec`)**:
    *   Spécifier le nom de l'application, la version, les dépendances Python (`requirements = python3,kivy,plyer,jinja2,requests` ou `httpx`).
    *   Inclure les fichiers et dossiers nécessaires (scripts Python, fichiers `.kv`, images, polices si utilisées localement).
    *   Configurer les permissions requises (ex: accès internet, stockage).
*   **Compilation**:
    ```bash
    buildozer android debug deploy run # Exemple pour Android
    buildozer ios debug deploy run    # Exemple pour iOS (nécessite macOS et Xcode)
    ```
*   **Distribution**:
    *   **Android**: Via le Google Play Store, ou en distribuant directement le fichier `.apk`.
    *   **iOS**: Via l'App Store d'Apple (nécessite un compte développeur Apple).

### 2.3. Configuration de l'API Backend

*   L'application mobile doit être configurée pour pointer vers l'URL correcte de l'API RESTful hébergée par l'application de bureau. Cela peut être une IP et un port sur le réseau local, ou une adresse publiquement accessible si l'application de bureau est exposée à internet (avec les précautions de sécurité nécessaires).
*   Cette configuration peut être codée en dur (moins flexible) ou configurable par l'utilisateur dans les paramètres de l'application mobile.

## 3. Déploiement du Serveur API (FastAPI)

*   Le serveur FastAPI est intégré à l'application de bureau. Son "déploiement" est donc lié à celui de l'application de bureau.
*   **Accessibilité**:
    *   **Usage Local/LAN**: Si l'application mobile est utilisée uniquement sur le même réseau local que l'application de bureau, l'adresse IP locale de la machine exécutant l'application de bureau suffit. Le pare-feu de la machine hôte doit autoriser les connexions entrantes sur le port de l'API.
    *   **Usage Externe (Internet)**:
        *   Nécessite que la machine hébergeant l'application de bureau ait une adresse IP publique ou soit accessible via un nom de domaine.
        *   Configuration du routeur/pare-feu pour transférer les requêtes du port public vers le port de l'API sur la machine locale (Port Forwarding).
        *   **Sécurité Cruciale**: Utiliser HTTPS. Cela implique l'obtention d'un certificat SSL/TLS (ex: via Let's Encrypt) et la configuration d'Uvicorn pour l'utiliser, ou placer un reverse proxy (comme Nginx ou Caddy) devant l'application FastAPI pour gérer HTTPS.
        *   Mettre en place des mesures de sécurité robustes (authentification forte, surveillance des logs, limitation de débit si nécessaire).

## 4. Maintenance

### 4.1. Mises à Jour Logicielles

*   **Application Desktop/Mobile**:
    *   Un mécanisme de notification de mise à jour peut être envisagé (l'application vérifie périodiquement une URL pour la dernière version).
    *   Pour les exécutables, les utilisateurs devront télécharger et installer la nouvelle version.
    *   Pour les applications mobiles distribuées via les stores, les stores gèrent le processus de mise à jour.
*   **Dépendances Python**: Mettre à jour régulièrement les dépendances (via `pip install -U <package>` ou en mettant à jour `requirements.txt` et en réinstallant) pour bénéficier des correctifs de sécurité et des nouvelles fonctionnalités. Tester l'application après chaque mise à jour majeure de dépendance.

### 4.2. Base de Données

*   **Sauvegardes (Backups)**:
    *   Pour SQLite, la sauvegarde consiste simplement à copier le fichier de base de données (`client_manager_app.db`) dans un emplacement sécurisé.
    *   Automatiser ce processus si possible (ex: script planifié).
    *   La fréquence des sauvegardes dépend de la criticité des données et de la fréquence des modifications.
*   **Intégrité et Optimisation**:
    *   SQLite a des commandes `PRAGMA integrity_check` et `VACUUM` qui peuvent être utiles occasionnellement.
*   **Migrations de Schéma**:
    *   Si la structure de la base de données évolue (ajout de tables/colonnes, modifications), un outil de migration comme **Alembic** (souvent utilisé avec SQLAlchemy) est fortement recommandé.
    *   Sans outil de migration, les modifications manuelles du schéma sont risquées et peuvent entraîner une perte de données. Les migrations permettent des mises à jour de schéma versionnées et reproductibles.

### 4.3. Surveillance et Logs

*   **Application Desktop**:
    *   L'application génère des fichiers logs (ex: `client_manager_app.log`). Examiner ces logs pour diagnostiquer les erreurs.
    *   Configurer le niveau de logging (DEBUG, INFO, WARNING, ERROR) en fonction des besoins (développement vs production).
*   **Serveur API**:
    *   FastAPI/Uvicorn génèrent des logs d'accès et d'erreurs. Surveiller ces logs pour détecter les problèmes, les tentatives d'accès non autorisées, ou les performances.
*   **Application Mobile**: Mettre en place un système de logging qui peut être consulté par l'utilisateur pour le débogage, ou un système de rapport d'erreurs distant (ex: Sentry, Firebase Crashlytics) pour les applications en production.

### 4.4. Sécurité

*   **Mots de Passe**: S'assurer que les mots de passe des utilisateurs sont stockés de manière sécurisée (hachés avec un algorithme robuste comme bcrypt ou Argon2).
*   **API Security**:
    *   Utiliser HTTPS pour toute communication API externe.
    *   Valider toutes les entrées de l'API.
    *   Appliquer des permissions strictes sur les endpoints.
    *   Protéger contre les vulnérabilités courantes (OWASP Top 10).
*   **Dépendances**: Scanner régulièrement les dépendances pour les vulnérabilités connues (ex: avec `safety` ou des outils intégrés à GitHub).

### 4.5. Documentation

*   Maintenir à jour la documentation utilisateur et la documentation technique (y compris ce dossier de conception) à mesure que l'application évolue.

Ce guide fournit une base. Les spécificités du déploiement et de la maintenance dépendront de l'environnement cible et de l'échelle d'utilisation.
