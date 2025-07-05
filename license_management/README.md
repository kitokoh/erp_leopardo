# Module de Gestion de Licences

Ce module est responsable de la gestion des licences logicielles pour l'application. Il permet de vérifier la validité des licences des utilisateurs, d'activer de nouvelles licences (gratuites ou payantes), et de contrôler l'accès aux fonctionnalités en fonction du type de licence.

## Fonctionnalités Principales

1.  **Vérification de Licence** :
    *   À chaque connexion d'un utilisateur, sa licence est vérifiée.
    *   Si la licence n'est pas valide (expirée, absente, inactive), l'accès à l'application principale est restreint.
    *   Une boîte de dialogue (`LicenseDialog`) est présentée à l'utilisateur pour gérer sa licence.

2.  **Types de Licences** :
    *   **Gratuite (`gratuit`)** : Offerte automatiquement lors de la première utilisation (si éligible). Limitée dans le temps (ex: 30 jours) et liée à l'utilisateur et à un identifiant machine.
    *   **Limitée (`limite`)** : Donne accès à un sous-ensemble défini de fonctionnalités. Peut avoir une date d'expiration.
    *   **Complète (`complet`)** : Donne accès à toutes les fonctionnalités de l'application. Peut être illimitée ou avoir une date d'expiration.

3.  **Activation de Licence** :
    *   **Licence Gratuite** : Activée automatiquement via `license_management.manager.activate_free_license()` si l'utilisateur n'a pas de licence valide et n'a pas déjà bénéficié d'une licence gratuite sur la machine/compte concerné.
    *   **Licence Payante (Clé Signée)** : L'utilisateur saisit une clé de licence dans `LicenseDialog`. La fonction `license_management.manager.activate_license()` est appelée. Cette fonction :
        *   Vérifie la signature cryptographique de la clé en utilisant une clé publique embarquée.
        *   Extrait les paramètres de la licence (type, date d'expiration, fonctionnalités spécifiques) directement de la clé signée.
        *   Lie la clé activée à l'utilisateur et à un identifiant machine (`machine_info`) pour empêcher la réutilisation abusive sur d'autres machines (selon la politique de la clé).
        *   Les clés signées sont générées par un utilitaire externe (`utils/license_key_generator.py`) utilisant une clé privée correspondante.

4.  **Gestion Dynamique des Droits d'Accès (Feature Flagging)** :
    *   La fonction `license_management.manager.get_allowed_features()` retourne un ensemble de constantes de fonctionnalités (ex: `FEATURE_PROJECT_MANAGEMENT`) autorisées pour le type de licence actif de l'utilisateur. Ceci est basé sur une `LICENSE_FEATURES_MAP` définie dans le manager.
    *   L'interface principale (`main_window.DocumentManager`) utilise cet ensemble de fonctionnalités autorisées, en combinaison avec les permissions basées sur les rôles, pour afficher/masquer dynamiquement les actions, menus et modules correspondants.

## Structure du Module

*   **`cruds.py`** (`db/cruds/licenses_crud.py`) : Contient les fonctions d'accès à la base de données (Create, Read, Update, Delete) pour les enregistrements de licences dans la table `Licenses`.
*   **`__init__.py` (agit comme `manager.py`)** : Contient la classe `LicenseManager` avec la logique métier de plus haut niveau :
    *   Vérification de validité des licences.
    *   Activation des licences (gratuites et payantes/signées).
    *   Gestion des identifiants machine (maintenant via la bibliothèque `machineid`).
    *   Définition des constantes de fonctionnalités et de la `LICENSE_FEATURES_MAP`.
    *   Méthode `get_allowed_features()`.
    *   Chargement de la clé publique pour la vérification des licences signées.
*   **`ui.py`** (`license_management/ui.py`) : Contient la classe `LicenseDialog` pour l'interaction utilisateur.
*   **`README.md`** (ce fichier).
*   **Utilitaire de génération de clés (hors application principale)** : `utils/license_key_generator.py` est utilisé pour créer les clés de licence signées.

## Intégration

*   **Base de Données** : La table `Licenses` est définie dans `db/init_schema.py`.
*   **Authentification** :
    *   `auth/authentication.py` : La fonction `login()` appelle `license_manager.check_license_validity()` après une authentification réussie.
    *   `main.py` : Gère le flux après la connexion. Si la licence est invalide, `LicenseDialog` est affichée. Si l'utilisateur configure une licence valide, l'application continue ; sinon, elle se ferme. `DocumentManager` reçoit les informations de la licence active.
*   **Interface Utilisateur Principale** :
    *   `main_window.py` (`DocumentManager`) : Initialise `allowed_features` en fonction de la licence et utilise cette information dans `_apply_permissions()` pour contrôler l'accès aux modules.

## Demande de Nouvelle Licence via Service Externe

Une fonctionnalité a été ajoutée pour permettre aux utilisateurs de demander une nouvelle licence (de type "limite" ou "complet") directement depuis la `LicenseDialog`. Cette demande est envoyée à un service externe (serveur HTTP).

*   **Initiation de la Demande :**
    *   Dans la `LicenseDialog`, l'utilisateur sélectionne le type de licence souhaité et clique sur "Passer la Demande de Nouvelle Licence".
*   **Données Envoyées au Serveur :**
    *   La requête est un `POST` HTTP au format `JSON` contenant : `user_id`, `username`, `email`, détails de la licence actuelle (si existante), `requested_license_type`, `machine_info`, et `request_timestamp`. (Voir la définition de l'API dans le plan ou le code pour les détails exacts).
*   **Configuration de l'URL du Serveur :**
    *   L'URL du serveur de demandes de licences est configurée dans `config.py` via la constante `LICENSE_REQUEST_SERVER_URL`. Par défaut, elle pointe vers `http://127.0.0.1:5678/api/license/request` pour le serveur de simulation.
*   **Serveur de Simulation (`license_request_server.py`) :**
    *   Un script serveur Flask minimal est fourni à la racine du projet : `license_request_server.py`.
    *   Ce serveur écoute sur l'endpoint `/api/license/request`. Il loggue les demandes reçues et retourne une réponse JSON de succès simulée.
    *   **Pour lancer le serveur de simulation :**
        1.  Assurez-vous que `Flask` est installé (`pip install Flask`).
        2.  Exécutez `python license_request_server.py` depuis la racine du projet.
        3.  Le serveur démarrera (par défaut sur `http://127.0.0.1:5678`). Laissez ce terminal ouvert pendant que vous testez la fonctionnalité dans l'application.
*   **Dépendances :** La fonctionnalité de demande de licence dans `LicenseDialog` utilise la bibliothèque `requests`. Assurez-vous qu'elle est installée (`pip install requests`) et listée dans `requirements.txt`.

## Informations Techniques

*   **Identifiant Machine** : La fonction `get_machine_identifier()` dans le `LicenseManager` utilise désormais la bibliothèque `machineid` pour tenter d'obtenir un identifiant unique et stable de la machine. Ceci est utilisé pour lier les licences activées à une machine spécifique.
*   **Clés de Licence (Payantes/Signées)** :
    *   Les clés de licence payantes sont désormais des **clés signées cryptographiquement (RSA-PSS avec SHA256)**.
    *   Chaque clé contient des données JSON embarquées (type de licence, date d'expiration, fonctionnalités spécifiques, etc.) et une signature.
    *   L'application vérifie la signature à l'aide d'une clé publique stockée.
    *   Un utilitaire `utils/license_key_generator.py` (avec une clé privée correspondante) est utilisé pour générer ces clés.
    *   Lors de l'activation, la clé signée complète est stockée dans la base de données, et une vérification est faite pour s'assurer que la même clé n'est pas réactivée sur la même machine par un autre utilisateur (selon la politique définie).
*   **Feature Flagging**: L'accès aux différentes fonctionnalités et modules de l'application est contrôlé dynamiquement par la combinaison du type de licence de l'utilisateur (via `LICENSE_FEATURES_MAP` dans `LicenseManager`) et de ses permissions basées sur son rôle.

## Pour les Développeurs

*   Lors de l'ajout de nouveaux modules/fonctionnalités soumis à licence, définissez une nouvelle constante `FEATURE_...` dans `license_management/__init__.py`.
*   Mettez à jour `LICENSE_FEATURES_MAP` dans `license_management.manager.py` pour spécifier quels types de licence donnent accès à cette nouvelle fonctionnalité.
*   Dans `main_window.py`, mettez à jour `MODULE_TO_LICENSE_FEATURE_MAP` si le nouveau module doit être contrôlé par la licence.
*   Utilisez `self.allowed_features` dans `DocumentManager` ou passez cette information aux widgets concernés pour conditionner l'affichage ou l'activation de l'interface utilisateur de la fonctionnalité.

## Gestion des Clés (Hors Scope Actuel)

La génération, la distribution, et la révocation des clés de licence payantes (par exemple, via un portail web ou un serveur de licences) ne sont pas gérées par ce module. Ce module se concentre sur l'application et la vérification locale des licences une fois qu'une clé est fournie ou qu'une licence gratuite est activée.
