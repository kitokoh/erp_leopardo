# Module : Gestion des Utilisateurs et Authentification

## 1. Introduction et Objectifs

Ce module est responsable de la création des comptes utilisateurs, de leur authentification sécurisée au sein de l'application web, de la gestion de leurs informations de profil, et potentiellement de la gestion des droits d'accès basiques. Il constitue la porte d'entrée de l'application.

**Objectifs Clés :**

*   Permettre aux nouveaux utilisateurs de s'inscrire.
*   Permettre aux utilisateurs existants de se connecter et se déconnecter.
*   Assurer la sécurité des mots de passe et des sessions.
*   Permettre aux utilisateurs de consulter et modifier certaines informations de leur profil.
*   Fournir les bases pour la gestion des permissions dans les autres modules.

## 2. Modèles de Données Associés

*   **`users.User (django.contrib.auth.models.AbstractUser)`** : Modèle principal pour les utilisateurs.
    *   Champs hérités : `username`, `password`, `email`, `first_name`, `last_name`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`.
    *   Champs personnalisés potentiels (si non gérés dans un modèle `Profile` séparé) : `phone_number`, `profile_picture`.
    *   Relation implicite avec `authtoken.Token` (créé par DRF).
*   **`users.Company`** : (Défini dans `00_architecture_globale.md` et sera détaillé dans `02_societes_gestion.md`)
    *   `owner = models.ForeignKey(User, related_name='owned_companies', on_delete=models.CASCADE)` : Un utilisateur est propriétaire d'une ou plusieurs sociétés. Lors de l'inscription, une société par défaut sera créée pour l'utilisateur.

## 3. Spécifications de l'API (Endpoints DRF pertinents)

Les détails complets des serializers et vues API se trouvent dans `06_api_specifications_drf.md`. Voici un résumé des endpoints clés pour ce module :

*   **`POST /api/users/register/`** : Inscription d'un nouvel utilisateur.
*   **`POST /api/users/login/`** : Connexion d'un utilisateur et obtention d'un token d'authentification.
*   **`GET /api/users/me/`** : Récupérer les informations de l'utilisateur actuellement authentifié.
*   **`PUT /api/users/me/`** : Mettre à jour les informations de l'utilisateur actuellement authentifié.
*   **`POST /api/users/logout/` (Optionnel pour TokenAuth simple)** : Si une invalidation de token côté serveur est implémentée. Sinon, la déconnexion est gérée côté client par la suppression du token.
*   **`POST /api/users/password/change/`** : Changement de mot de passe pour un utilisateur authentifié.
*   **`POST /api/users/password/reset/`** : Demande de réinitialisation de mot de passe (envoi d'email).
*   **`POST /api/users/password/reset/confirm/`** : Confirmation de la réinitialisation avec un token.

## 4. Fonctionnalités Détaillées

### 4.1. Inscription d'un Nouvel Utilisateur

*   **Cas d'Utilisation (User Story)** : "En tant que visiteur non authentifié, je veux créer un compte utilisateur pour accéder aux fonctionnalités de l'application."
*   **Préconditions** : L'utilisateur n'est pas déjà connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur clique sur un lien/bouton "S'inscrire" ou "Créer un compte".
    2.  **Interface Utilisateur (Page `/auth/register/`)** :
        *   **URL** : `/auth/register/` (nom de la vue Django : `user_register_view`)
        *   **Template** : `users/register.html`
        *   **Formulaire** :
            *   Champ "Nom d'utilisateur" (`username`): Texte, requis, unique.
            *   Champ "Adresse Email" (`email`): Email, requis, unique.
            *   Champ "Prénom" (`first_name`): Texte, optionnel.
            *   Champ "Nom de famille" (`last_name`): Texte, optionnel.
            *   Champ "Mot de passe" (`password`): Password, requis.
            *   Champ "Confirmer le mot de passe" (`password2`): Password, requis.
            *   (Optionnel) Champ "Nom de votre société" (`company_name`): Texte, requis. Si non fourni ici, un nom par défaut sera généré.
            *   Bouton "S'inscrire".
        *   **Affichage des Erreurs** : Les erreurs de validation du formulaire (ex: email invalide, mots de passe non identiques, nom d'utilisateur déjà pris) sont affichées à côté des champs concernés ou en haut du formulaire.
    3.  **Logique Backend (Vue Django `users.views.UserRegisterView`)** :
        *   Méthode `GET` : Affiche le formulaire d'inscription vide (basé sur `users.forms.UserRegistrationForm`).
        *   Méthode `POST` :
            *   Récupère les données du formulaire soumis.
            *   Valide les données en utilisant `UserRegistrationForm`.
            *   Si le formulaire est valide :
                *   Appelle l'endpoint API `POST /api/users/register/` avec les données `username`, `email`, `password`, `first_name`, `last_name`.
                *   L'API DRF (via `UserRegistrationSerializer`) crée l'objet `User`.
                *   L'API DRF crée également une `Company` par défaut pour cet utilisateur (ex: "Société de [username]" ou utilise le `company_name` fourni). L'utilisateur devient `owner` de cette société.
                *   L'API DRF génère un token d'authentification pour le nouvel utilisateur.
                *   La vue Django reçoit la réponse de l'API (contenant les infos utilisateur et le token).
                *   Connecte automatiquement l'utilisateur dans la session Django (en utilisant `django.contrib.auth.login`).
                *   Stocke le token reçu de l'API dans la session de l'utilisateur (ou un cookie HTTPOnly sécurisé) pour les futurs appels API depuis le backend Django.
            *   Si l'appel API réussit : Redirige l'utilisateur vers la page du tableau de bord (`/dashboard/`). Affiche un message de succès (ex: "Bienvenue ! Votre compte a été créé avec succès.").
            *   Si le formulaire n'est pas valide ou si l'appel API retourne une erreur (ex: email déjà utilisé) : Ré-affiche le formulaire avec les erreurs.
    4.  **Interactions HTMX/Alpine.js** :
        *   Optionnel : La validation des champs pourrait se faire via des appels HTMX partiels à des endpoints de validation spécifiques pour une meilleure UX, avant la soumission complète.
*   **Flux Alternatifs et Exceptions** :
    *   Email déjà utilisé : Message d'erreur clair.
    *   Nom d'utilisateur déjà utilisé : Message d'erreur clair.
    *   Mots de passe ne correspondent pas : Message d'erreur.
    *   Problème de communication avec l'API DRF (si la vue Django appelle l'API) : Message d'erreur générique.
*   **Postconditions** :
    *   Un nouvel objet `User` est créé et actif.
    *   Un nouvel objet `Company` est créé et lié à l'utilisateur comme `owner`.
    *   Un `Token` d'authentification est créé pour l'utilisateur.
    *   L'utilisateur est connecté et redirigé vers le tableau de bord.
*   **Permissions Requises** : Aucune (accès public).

### 4.2. Connexion d'un Utilisateur Existant

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur enregistré, je veux me connecter à l'application avec mon nom d'utilisateur et mon mot de passe."
*   **Préconditions** : L'utilisateur a un compte existant et n'est pas déjà connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur clique sur "Se connecter".
    2.  **Interface Utilisateur (Page `/auth/login/`)** :
        *   **URL** : `/auth/login/` (nom de la vue Django : `user_login_view`)
        *   **Template** : `users/login.html`
        *   **Formulaire** :
            *   Champ "Nom d'utilisateur" ou "Email" (`login`): Texte, requis.
            *   Champ "Mot de passe" (`password`): Password, requis.
            *   (Optionnel) Case à cocher "Se souvenir de moi".
            *   Bouton "Se connecter".
            *   Lien "Mot de passe oublié ?".
    3.  **Logique Backend (Vue Django `users.views.UserLoginView`)** :
        *   Méthode `GET` : Affiche le formulaire de connexion vide (basé sur `django.contrib.auth.forms.AuthenticationForm` ou un formulaire personnalisé).
        *   Méthode `POST` :
            *   Récupère les données du formulaire.
            *   Valide les identifiants :
                *   Option 1 (Authentification Django directe) : Utilise `django.contrib.auth.authenticate()` puis `django.contrib.auth.login()`. Si succès, fait un appel à l'endpoint `/api/users/login/` (ou un endpoint `/api/users/me/token/`) pour obtenir/rafraîchir un token DRF et le stocker en session/cookie pour les appels API ultérieurs par le backend Django.
                *   Option 2 (Authentification via API DRF) : Appelle directement l'endpoint API `POST /api/users/login/` (qui utilise `ObtainAuthToken` de DRF). L'API valide les identifiants.
            *   Si l'authentification (via Django ou API) réussit :
                *   La vue Django reçoit les informations utilisateur et le token (si Option 2).
                *   Connecte l'utilisateur dans la session Django (si ce n'est pas déjà fait par `authenticate/login`).
                *   Stocke le token DRF dans la session de l'utilisateur ou un cookie sécurisé.
                *   Redirige vers la page demandée avant la connexion (si `next` param est présent) ou vers le tableau de bord (`/dashboard/`).
            *   Si l'authentification échoue : Ré-affiche le formulaire avec un message d'erreur global (ex: "Nom d'utilisateur ou mot de passe incorrect.").
    4.  **Interactions HTMX/Alpine.js** : Non critiques pour ce formulaire, mais pourraient être utilisées pour afficher des messages d'erreur de manière plus dynamique.
*   **Flux Alternatifs et Exceptions** :
    *   Identifiants incorrects : Message d'erreur.
    *   Compte inactif ou bloqué : Message approprié.
*   **Postconditions** :
    *   L'utilisateur est connecté.
    *   La session Django est active.
    *   Un token DRF est disponible (stocké côté serveur en session ou dans un cookie) pour le backend Django.
    *   L'utilisateur est redirigé.
*   **Permissions Requises** : Aucune (accès public).

### 4.3. Déconnexion d'un Utilisateur

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur connecté, je veux me déconnecter de l'application."
*   **Préconditions** : L'utilisateur est connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur clique sur "Se déconnecter".
    2.  **Interface Utilisateur** : L'action est généralement initiée par un lien ou un bouton dans la barre de navigation ou le menu utilisateur.
        *   **URL** : `/auth/logout/` (nom de la vue Django : `user_logout_view`)
    3.  **Logique Backend (Vue Django `users.views.UserLogoutView`)** :
        *   Appelle `django.contrib.auth.logout(request)` pour terminer la session Django.
        *   Supprime le token DRF stocké en session ou dans le cookie.
        *   Optionnel : Si une invalidation de token côté serveur est implémentée pour DRF (ex: via une table de tokens blacklistés), appelle l'endpoint API `/api/users/logout/` pour invalider le token actuel.
        *   Redirige l'utilisateur vers la page d'accueil ou la page de connexion.
        *   Affiche un message de succès (ex: "Vous avez été déconnecté.").
*   **Postconditions** :
    *   L'utilisateur est déconnecté.
    *   La session Django est détruite.
    *   Le token DRF est invalidé/supprimé côté client (et potentiellement côté serveur).
*   **Permissions Requises** : Utilisateur authentifié.

### 4.4. Consultation et Modification du Profil Utilisateur

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur connecté, je veux consulter et modifier mes informations de profil (ex: email, prénom, nom)."
*   **Préconditions** : L'utilisateur est connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur accède à sa page de profil (ex: via un menu "Mon Compte").
    2.  **Interface Utilisateur (Page `/auth/profile/`)** :
        *   **URL** : `/auth/profile/` (nom de la vue Django : `user_profile_view`)
        *   **Template** : `users/profile.html`
        *   **Affichage (Mode Consultation)** :
            *   Nom d'utilisateur (lecture seule).
            *   Email.
            *   Prénom.
            *   Nom de famille.
            *   (Autres champs si définis : téléphone, photo de profil).
            *   Bouton "Modifier le profil".
            *   Lien "Changer le mot de passe".
        *   **Formulaire (Mode Édition, après clic sur "Modifier")** :
            *   Champs pré-remplis avec les valeurs actuelles pour email, prénom, nom.
            *   Bouton "Enregistrer les modifications".
            *   Bouton "Annuler".
    3.  **Logique Backend (Vue Django `users.views.UserProfileView`)** :
        *   Méthode `GET` :
            *   Récupère l'utilisateur connecté (`request.user`).
            *   Peut appeler l'endpoint API `GET /api/users/me/` pour obtenir les données les plus à jour si nécessaire (ou utiliser directement `request.user`).
            *   Passe les données utilisateur et un formulaire (ex: `UserProfileForm` initialisé avec l'instance `request.user`) au template.
        *   Méthode `POST` (pour la mise à jour) :
            *   Récupère les données du formulaire soumis.
            *   Valide les données avec `UserProfileForm`.
            *   Si valide :
                *   Appelle l'endpoint API `PUT /api/users/me/` avec les données modifiées.
                *   L'API DRF met à jour l'objet `User`.
                *   Si succès de l'API : Affiche un message de succès. Redirige vers la page de profil (mode consultation) ou reste sur la page avec un message.
            *   Si invalide ou erreur API : Ré-affiche le formulaire avec les erreurs.
    4.  **Interactions HTMX/Alpine.js** :
        *   Alpine.js peut être utilisé pour basculer entre le mode consultation et le mode édition du profil sur la même page.
        *   HTMX peut être utilisé pour soumettre le formulaire de mise à jour et afficher les messages de succès/erreur sans rechargement complet.
*   **Flux Alternatifs et Exceptions** :
    *   Validation échouée (ex: email invalide) : Message d'erreur.
    *   Erreur de l'API lors de la mise à jour : Message d'erreur.
*   **Postconditions** :
    *   Les informations de l'utilisateur sont mises à jour en base de données.
    *   L'utilisateur voit les informations mises à jour.
*   **Permissions Requises** : Utilisateur authentifié (ne peut modifier que son propre profil).

### 4.5. Changement de Mot de Passe (Utilisateur Connecté)

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur connecté, je veux changer mon mot de passe."
*   **Préconditions** : L'utilisateur est connecté.
*   **Flux Nominal (Scénario Principal)** :
    1.  **Déclencheur** : L'utilisateur accède à la page "Changer de mot de passe" (souvent depuis sa page de profil).
    2.  **Interface Utilisateur (Page `/auth/password/change/`)** :
        *   **URL** : `/auth/password/change/`
        *   **Template** : `users/password_change_form.html`
        *   **Formulaire** (utilisant `django.contrib.auth.forms.PasswordChangeForm` ou un équivalent personnalisé) :
            *   Champ "Ancien mot de passe".
            *   Champ "Nouveau mot de passe".
            *   Champ "Confirmer le nouveau mot de passe".
            *   Bouton "Changer le mot de passe".
    3.  **Logique Backend (Vue Django)** :
        *   Méthode `GET` : Affiche le formulaire.
        *   Méthode `POST` :
            *   Valide le formulaire. `PasswordChangeForm` vérifie l'ancien mot de passe et que les nouveaux correspondent.
            *   Si valide :
                *   Appelle l'endpoint API `POST /api/users/password/change/` avec l'ancien et le nouveau mot de passe.
                *   L'API DRF met à jour le mot de passe de l'utilisateur.
                *   Si succès : Déconnecte potentiellement l'utilisateur (bonne pratique de sécurité) ou met à jour la session avec le nouveau hash de mot de passe. Affiche un message de succès. Redirige vers la page de profil ou de connexion.
            *   Si invalide : Ré-affiche le formulaire avec les erreurs.
*   **Postconditions** : Le mot de passe de l'utilisateur est changé. La session peut être invalidée.
*   **Permissions Requises** : Utilisateur authentifié.

### 4.6. Réinitialisation de Mot de Passe (Mot de Passe Oublié)

*   **Cas d'Utilisation (User Story)** : "En tant qu'utilisateur ayant oublié mon mot de passe, je veux pouvoir le réinitialiser via mon adresse email."
*   **Préconditions** : L'utilisateur n'est pas connecté (ou ne peut pas se connecter).
*   **Flux Nominal (Scénario Principal)** :
    1.  **Demande de Réinitialisation**
        *   **Déclencheur** : Clic sur "Mot de passe oublié ?" sur la page de connexion.
        *   **Interface Utilisateur (Page `/auth/password/reset/`)** :
            *   Formulaire avec un champ "Adresse Email". Bouton "Envoyer le lien de réinitialisation".
        *   **Logique Backend (Vue Django)** :
            *   POST : Valide l'email. Appelle l'API `POST /api/users/password/reset/` avec l'email.
            *   L'API DRF génère un token de réinitialisation, le stocke, et envoie un email à l'utilisateur avec un lien contenant ce token.
            *   Affiche un message confirmant que si l'email existe, un lien a été envoyé.
    2.  **Confirmation de Réinitialisation**
        *   **Déclencheur** : L'utilisateur clique sur le lien dans l'email. Ce lien mène à une page comme `/auth/password/reset/confirm/<uidb64>/<token>/`.
        *   **Interface Utilisateur (Page `/auth/password/reset/confirm/...`)** :
            *   Formulaire avec champs "Nouveau mot de passe" et "Confirmer le nouveau mot de passe".
        *   **Logique Backend (Vue Django)** :
            *   GET : Valide l'UID et le token du lien. Si valides, affiche le formulaire de saisie du nouveau mot de passe.
            *   POST : Valide les nouveaux mots de passe. Appelle l'API `POST /api/users/password/reset/confirm/` avec UID, token, et nouveau mot de passe.
            *   L'API DRF valide le token et met à jour le mot de passe.
            *   Si succès : Affiche un message de succès. Redirige vers la page de connexion.
*   **Postconditions** : Le mot de passe de l'utilisateur est réinitialisé.
*   **Permissions Requises** : Aucune (accès public).

---

Ce document sera la base pour le développement du module de gestion des utilisateurs et d'authentification. Les détails des templates HTML et des interactions HTMX/Alpine.js spécifiques seront affinés lors de l'écriture du code, mais les principes directeurs sont établis ici.
Les autres fichiers (`02_societes_gestion.md`, etc.) seront créés vides pour l'instant.
