# Module : Paramètres et Configuration (Desktop)

## 1. Objectif Principal

Le module de Paramètres et Configuration de ClientDocManager a pour but de permettre aux administrateurs et/ou utilisateurs habilités de personnaliser et de configurer divers aspects de l'application pour l'adapter aux besoins spécifiques de l'entreprise et aux préférences des utilisateurs. Cela inclut la gestion des informations de l'entreprise, la configuration des modèles de documents, la gestion des langues, et d'autres paramètres généraux de l'application.

## 2. Composants Clés et Fonctionnalités

*   **Page des Paramètres (`settings_page.py`)**:
    *   Interface utilisateur principale pour accéder aux différentes sections de configuration.
    *   Typiquement organisée en onglets ou en catégories pour une navigation aisée (ex: Général, Informations Entreprise, Modèles, Utilisateurs, Langues, API, etc.).

*   **Gestion des Informations de l'Entreprise (`company_profile_dialog.py`, `company_management.py`)**:
    *   Saisie et modification des informations de l'entreprise de l'utilisateur de l'application (nom, adresse, logo, numéros fiscaux, informations bancaires).
    *   Ces informations sont utilisées pour remplir automatiquement les en-têtes et pieds de page des documents officiels (factures, devis).
    *   Interaction avec `db/cruds/companies_crud.py`.

*   **Gestion des Modèles de Documents**:
    *   **`template_dialog.py`**: Interface pour gérer les modèles de documents (Word `.docx`, HTML `.html`, Excel `.xlsx`).
    *   Téléchargement de nouveaux modèles.
    *   Prévisualisation (potentiellement simplifiée) ou modification des modèles existants (peut ouvrir l'éditeur par défaut du système).
    *   Assignation de modèles par défaut pour certains types de documents.
    *   Gestion des langues pour les modèles.
    *   Stockage des modèles dans le dossier `templates/` (organisé par langue) et référencement en base de données via `db/cruds/templates_crud.py` (ou `cover_page_templates_crud.py` pour les pages de garde).
    *   **`initial_setup_dialog.py`** et **`app_setup.py` (`initialize_default_templates`)**: Logique pour s'assurer que les modèles par défaut existent sur le disque au premier lancement ou lors de la configuration initiale.

*   **Configuration de la Langue de l'Application**:
    *   Sélection de la langue d'affichage de l'interface utilisateur de l'application.
    *   Les traductions sont gérées via les fichiers `.qm` dans `translations/qm/` et les fichiers sources `.ts` dans `translations/ts/`.
    *   Le paramètre de langue est sauvegardé (probablement via `db/cruds/application_settings_crud.py` avec une clé comme `user_selected_language`).

*   **Gestion des Paramètres Généraux de l'Application**:
    *   **`app_setup.py` (`CONFIG`, `save_config`)**: Gestion d'un fichier de configuration (ex: `config.json` ou similaire) pour les paramètres qui ne sont pas stockés en base de données ou qui sont nécessaires très tôt au démarrage.
        *   Chemins des répertoires (modèles, clients).
        *   Paramètres de connexion API (si l'application consomme des API externes).
        *   Options de comportement par défaut.
    *   **`db/cruds/application_settings_crud.py`**: CRUD pour stocker et récupérer des paires clé-valeur de paramètres directement en base de données. Cela permet une configuration dynamique sans redémarrage de l'application pour certains paramètres.
    *   Configuration du serveur SMTP pour l'envoi d'e-mails (via `email_service.py`, qui pourrait avoir sa propre configuration ou utiliser des paramètres stockés).

*   **Paramètres de Sécurité (`security_settings_page.py`)**:
    *   Options liées à la sécurité, comme la politique de mot de passe (longueur minimale, complexité - si géré dynamiquement).
    *   Configuration de l'authentification biométrique (`security_module/biometric_auth.py`) si applicable.
    *   Gestion des sessions (durée de session, timeout - `SESSION_TIMEOUT_SECONDS` dans `main.py` est actuellement codé en dur mais pourrait devenir configurable).

*   **Configuration de l'API (si l'application en expose une)**:
    *   Paramètres du serveur API FastAPI (port, host - bien que souvent configurés au démarrage).

*   **Configuration Initiale (`initial_setup_dialog.py`)**:
    *   Un dialogue présenté au premier lancement de l'application pour guider l'utilisateur à travers les configurations essentielles (création de l'entreprise principale, chemins des dossiers, etc.).
    *   Marque la configuration initiale comme complète pour ne pas réapparaître (`utils.mark_initial_setup_complete`).

## 3. Flux de Travail Typique

### 3.1. Modification des Informations de l'Entreprise

1.  L'administrateur accède à la `SettingsPage`.
2.  Il sélectionne la section "Informations de l'Entreprise".
3.  Le `CompanyProfileDialog` s'ouvre, affichant les informations actuelles.
4.  L'administrateur modifie les données (ex: nouvelle adresse, nouveau logo).
5.  Après validation, `companies_crud.update_company()` est appelé pour sauvegarder les modifications en base de données.
6.  Les documents futurs utiliseront ces nouvelles informations.

### 3.2. Ajout d'un Nouveau Modèle de Document

1.  L'administrateur accède à la section "Gestion des Modèles" dans `SettingsPage`.
2.  Il utilise `TemplateDialog` (ou une interface similaire) pour télécharger un nouveau fichier modèle (ex: un `.docx` pour les contrats).
3.  Il spécifie le type de document, la langue, et un nom pour le modèle.
4.  Le fichier modèle est copié dans le dossier `templates/` approprié.
5.  Une entrée est créée dans la base de données via `templates_crud.add_template()` pour référencer ce modèle.

### 3.3. Changement de la Langue de l'Application

1.  L'utilisateur accède à la section "Langue" ou "Général" dans `SettingsPage`.
2.  Il sélectionne une nouvelle langue dans une liste déroulante.
3.  Le choix est sauvegardé via `application_settings_crud.save_setting('user_selected_language', new_lang_code)`.
4.  L'application informe l'utilisateur qu'un redémarrage peut être nécessaire pour que tous les changements prennent effet (ou tente de recharger les traducteurs dynamiquement si possible).

## 4. Interactions avec d'Autres Modules

*   **Tous les modules**: De nombreux modules dépendent des paramètres configurés ici.
    *   **Gestion Client (pour la partie documents)**: Utilise les informations de l'entreprise, les modèles de documents (gérés ici ou dans "Gestion Client"), les paramètres de langue pour le contenu.
    *   **Facturation et Paiements**: Utilise les informations de l'entreprise, les taux de TVA par défaut, les modèles de facture.
    *   **Gestion des E-mails**: Utilise la configuration SMTP (si elle est gérée ici).
    *   **Authentification**: La durée de session ou les politiques de mot de passe peuvent être configurées ici.
    *   **Internationalisation**: L'ensemble de l'application utilise le paramètre de langue pour afficher l'UI.
*   **Base de Données**: Stocke de nombreux paramètres (informations entreprise, références des modèles, paramètres d'application).
*   **Système de Fichiers**: Pour le stockage des modèles de documents, logos, etc.

## 5. Points d'Attention

*   **Impact des Modifications**: Certaines modifications de paramètres peuvent avoir un impact important sur le fonctionnement de l'application ou sur les données existantes. Des avertissements ou des confirmations peuvent être nécessaires.
*   **Permissions d'Accès**: L'accès à la page des paramètres, et surtout à certaines sections critiques (comme la gestion des utilisateurs ou les informations de l'entreprise), doit être restreint aux administrateurs ou utilisateurs habilités.
*   **Validation des Entrées**: Les valeurs saisies pour les paramètres doivent être validées pour éviter les erreurs de configuration.
*   **Facilité d'Utilisation**: Même si cette section est souvent destinée aux administrateurs, elle doit rester aussi claire et intuitive que possible.
*   **Sauvegarde et Restauration de la Configuration**: Pour les configurations complexes, une fonctionnalité d'export/import des paramètres pourrait être utile.
*   **Documentation des Paramètres**: Chaque paramètre devrait idéalement être accompagné d'une brève description de son rôle et de son impact.
