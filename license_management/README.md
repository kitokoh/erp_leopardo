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
    *   **Licence Payante** : L'utilisateur saisit une clé de licence dans `LicenseDialog`. La fonction `license_management.manager.activate_license()` est appelée pour valider et activer la clé. (La validation de la clé elle-même par rapport à un système externe de génération/vente de clés n'est pas dans le scope de ce module, qui se concentre sur l'application locale de la licence).

4.  **Gestion des Droits d'Accès** :
    *   La fonction `license_management.manager.get_allowed_features()` retourne un ensemble de chaînes représentant les fonctionnalités autorisées pour la licence active de l'utilisateur.
    *   L'interface principale (`main_window.DocumentManager`) utilise ces informations, en combinaison avec les permissions basées sur les rôles, pour afficher/masquer les actions et modules correspondants.

## Structure du Module

*   **`cruds.py`** : Contient les fonctions d'accès à la base de données (Create, Read, Update, Delete) pour les enregistrements de licences dans la table `Licenses`.
*   **`manager.py`** : Contient la logique métier de plus haut niveau pour la gestion des licences (génération de clé, identifiant machine, activation, vérification de validité, gestion des fonctionnalités).
*   **`ui.py`** : Contient la classe `LicenseDialog` (basée sur `QDialog`) qui est l'interface utilisateur pour que l'utilisateur puisse voir l'état de sa licence et en activer une nouvelle.
*   **`README.md`** : Ce fichier.

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

*   **Identifiant Machine** : La fonction `get_machine_identifier()` dans `manager.py` utilise une combinaison d'informations système (MAC address, nom d'hôte, processeur) hachées pour lier la licence gratuite. Cette méthode est basique et pourrait être renforcée pour des applications commerciales.
*   **Clés de Licence (Payantes)** : Ce module ne génère ni ne valide l'authenticité des clés payantes par rapport à un serveur externe. Il suppose que si une clé est fournie, sa validité intrinsèque (type, durée) est déterminée par une logique interne (ex: préfixe de la clé) ou qu'elle a été pré-validée. Une clé ne peut pas être activement utilisée par plusieurs utilisateurs simultanément.

## Pour les Développeurs

*   Lors de l'ajout de nouveaux modules/fonctionnalités soumis à licence, définissez une nouvelle constante `FEATURE_...` dans `license_management.manager.py`.
*   Mettez à jour `LICENSE_FEATURES_MAP` dans `license_management.manager.py` pour spécifier quels types de licence donnent accès à cette nouvelle fonctionnalité.
*   Dans `main_window.py`, mettez à jour `MODULE_TO_LICENSE_FEATURE_MAP` si le nouveau module doit être contrôlé par la licence.
*   Utilisez `self.allowed_features` dans `DocumentManager` ou passez cette information aux widgets concernés pour conditionner l'affichage ou l'activation de l'interface utilisateur de la fonctionnalité.

## Gestion des Clés (Hors Scope Actuel)

La génération, la distribution, et la révocation des clés de licence payantes (par exemple, via un portail web ou un serveur de licences) ne sont pas gérées par ce module. Ce module se concentre sur l'application et la vérification locale des licences une fois qu'une clé est fournie ou qu'une licence gratuite est activée.
