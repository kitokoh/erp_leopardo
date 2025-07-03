# Module : Authentification et Gestion des Utilisateurs (Desktop)

## 1. Objectif Principal

Ce module est responsable de la sécurisation de l'accès à l'application ClientDocManager. Il gère l'identification des utilisateurs, la vérification de leurs droits d'accès (permissions) en fonction de leurs rôles, et la gestion administrative de leurs comptes. L'objectif est de s'assurer que seuls les utilisateurs autorisés peuvent accéder à l'application et à ses fonctionnalités, conformément aux politiques de sécurité définies.

## 2. Composants Clés et Fonctionnalités

*   **Authentification des Utilisateurs**:
    *   **Dialogue de Connexion (`dialogs/login_dialog.py`)**: Interface graphique présentée au démarrage de l'application (sauf si une session "Se souvenir de moi" est active et valide) où l'utilisateur saisit son nom d'utilisateur et son mot de passe.
    *   **Service d'Authentification (`auth/authentication.py`)**: Contient la logique de vérification des informations d'identification.
        *   Compare le mot de passe fourni avec le hash stocké en base de données (utilisation de `bcrypt`).
        *   Gère la fonctionnalité "Se souvenir de moi" en stockant/récupérant potentiellement un jeton ou le nom d'utilisateur de manière sécurisée (via `QSettings` ou une méthode similaire).
        *   Gère la session utilisateur après une connexion réussie (par exemple, en stockant les informations de l'utilisateur connecté globalement dans l'application comme vu dans `main.py`).
    *   **Réinitialisation de Mot de Passe (`dialogs/reset_password_dialog.py`)**: Permet aux utilisateurs (probablement avec l'aide d'un administrateur ou via un mécanisme de récupération) de réinitialiser leur mot de passe.

*   **Gestion des Rôles (`auth/roles.py`)**:
    *   Définit les différents rôles utilisateurs au sein de l'application (ex: `SUPER_ADMIN`, `ADMIN`, `USER`, et potentiellement des rôles plus spécifiques comme `SALES_MANAGER`, `PROJECT_LEAD`, etc.).
    *   Chaque rôle est associé à un ensemble de permissions.
    *   Le fichier `roles.py` peut contenir les définitions statiques des rôles ou des fonctions pour les récupérer/gérer.

*   **Gestion des Permissions (`auth/permissions.py`)**:
    *   Définit les actions spécifiques que les utilisateurs peuvent effectuer dans l'application (ex: `CAN_CREATE_CLIENTS`, `CAN_DELETE_INVOICES`, `CAN_ACCESS_SETTINGS`).
    *   Lie les permissions aux rôles. Un utilisateur hérite des permissions du ou des rôle(s) qui lui sont assigné(s).
    *   Des fonctions ou des décorateurs peuvent être utilisés à travers l'application pour vérifier si l'utilisateur actuel a la permission requise avant d'autoriser une action ou d'afficher un composant UI.

*   **Gestion des Utilisateurs (`user_management/page.py`, `dialogs/user_dialog.py`, `dialogs/edit_user_dialog.py`)**:
    *   **Interface d'Administration des Utilisateurs**: Probablement une section dans les paramètres ou une page dédiée (`user_management/page.py`) permettant aux administrateurs de :
        *   Créer de nouveaux utilisateurs (spécifier nom d'utilisateur, mot de passe initial, assigner des rôles).
        *   Modifier les informations des utilisateurs existants.
        *   Activer/désactiver des comptes utilisateurs.
        *   Assigner/modifier les rôles des utilisateurs.
    *   **Dialogues de Création/Édition (`dialogs/user_dialog.py`, `dialogs/edit_user_dialog.py`)**: Interfaces spécifiques pour la saisie des informations utilisateur.

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/users_crud.py`**: Contient les fonctions CRUD pour interagir avec la table des utilisateurs en base de données (créer, lire, mettre à jour, supprimer des utilisateurs).
    *   **`db/cruds/roles_crud.py`** (si les rôles sont dynamiques et stockés en BD) et **`db/cruds/permissions_crud.py`** (si les permissions sont dynamiques).
    *   **`db/models/users.py`** (et potentiellement `roles.py`, `permissions.py` dans `db/models/`): Définitions des modèles SQLAlchemy pour les tables correspondantes.

*   **Sécurité des Mots de Passe**:
    *   Utilisation de `bcrypt` pour le hachage et le salage des mots de passe, assurant qu'ils ne sont pas stockés en clair.

## 3. Flux de Travail Typique

### 3.1. Connexion d'un Utilisateur

1.  L'application démarre, `main.py` lance le `LoginDialog`.
2.  L'utilisateur saisit son nom d'utilisateur et son mot de passe. Coche éventuellement "Se souvenir de moi".
3.  Le `LoginDialog` appelle `auth_service.login(username, password, remember_me)`.
4.  `auth_service.login` récupère l'utilisateur depuis la base de données via `users_crud.get_user_by_username()`.
5.  Si l'utilisateur existe et est actif, `auth_service` vérifie le mot de passe en utilisant `bcrypt.checkpw()`.
6.  Si la vérification réussit :
    *   Les informations de l'utilisateur (ID, rôle(s)) sont stockées globalement (par exemple, dans `main.CURRENT_USER_ID`, `main.CURRENT_USER_ROLE`).
    *   Si "Se souvenir de moi" est coché, `auth_service.save_remember_me_preference()` est appelé.
    *   Le `LoginDialog` se ferme avec un statut `Accepted`.
7.  `main.py` procède à l'affichage de la fenêtre principale `DocumentManager`.
8.  Si la vérification échoue, un message d'erreur est affiché dans le `LoginDialog`.

### 3.2. Création d'un Nouvel Utilisateur (par un Administrateur)

1.  Un administrateur accède à la page de gestion des utilisateurs (`user_management/page.py`).
2.  L'administrateur clique sur "Créer un utilisateur".
3.  Le `UserDialog` s'ouvre.
4.  L'administrateur saisit les informations du nouvel utilisateur (nom d'utilisateur, mot de passe, e-mail, etc.) et lui assigne un ou plusieurs rôles.
5.  À la validation, les données sont envoyées à une fonction (par exemple, dans `users_crud.py` ou via un service dans `auth/`).
6.  Le mot de passe est haché avec `bcrypt`.
7.  Le nouvel utilisateur est inséré en base de données avec ses rôles.
8.  L'interface est mise à jour pour refléter l'ajout.

### 3.3. Vérification des Permissions

1.  Un utilisateur tente d'accéder à une fonctionnalité ou d'effectuer une action.
2.  Avant d'exécuter l'action, le code (par exemple, un gestionnaire d'événement dans l'UI ou une méthode de service) vérifie les permissions de l'utilisateur connecté.
3.  Cela peut impliquer de récupérer le rôle de l'utilisateur (stocké en session) et de consulter `auth/permissions.py` (ou la base de données) pour voir si ce rôle a la permission requise.
4.  Si l'utilisateur a la permission, l'action est autorisée. Sinon, elle est bloquée et un message d'erreur ou un avertissement peut être affiché.

## 4. Interactions avec d'Autres Modules

*   **Tous les autres modules fonctionnels**: Le module d'authentification et de gestion des utilisateurs est transversal. L'accès à quasiment toutes les fonctionnalités de l'application est conditionné par les permissions de l'utilisateur connecté.
*   **Base de Données**: Stocke toutes les informations relatives aux utilisateurs, à leurs rôles (si dynamiques), et potentiellement aux permissions (si dynamiques).
*   **`main.py`**: Orchestre le flux de connexion initial et stocke les informations de la session utilisateur active.
*   **Journalisation/Audit (Logging)**: Les tentatives de connexion (réussies ou échouées) et les actions de gestion des utilisateurs devraient être journalisées pour des raisons de sécurité et d'audit.

## 5. Points d'Attention

*   **Sécurité des Mots de Passe**: Le hachage robuste des mots de passe est crucial. `bcrypt` est un bon choix.
*   **Gestion des Sessions**: La manière dont les informations de session sont maintenues et sécurisées (surtout pour "Se souvenir de moi") est importante.
*   **Principe du Moindre Privilège**: Les utilisateurs ne devraient se voir accorder que les permissions strictement nécessaires à l'accomplissement de leurs tâches.
*   **Complexité des Mots de Passe**: Des politiques de complexité des mots de passe peuvent être envisagées.
*   **Protection contre les Attaques**: Mécanismes contre les attaques par force brute sur le dialogue de connexion (par exemple, limitation du nombre de tentatives).
*   **Audit Trail**: Journalisation des actions sensibles (création/modification d'utilisateurs, changements de rôles).
