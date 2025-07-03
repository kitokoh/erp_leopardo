# Module : Gestion des E-mails (Interface Utilisateur - Desktop)

## 1. Objectif Principal

Ce document décrit les aspects de l'interface utilisateur (UI) du ClientDocManager qui permettent aux utilisateurs d'envoyer des e-mails directement depuis l'application et potentiellement de gérer des modèles d'e-mails. Tandis que le `email_service.py` (décrit dans [Module Utilitaires et Services Transverses](./module_utilitaires_services.md)) gère la logique d'envoi backend, ce module se concentre sur l'expérience utilisateur pour composer, prévisualiser et envoyer ces e-mails.

## 2. Composants Clés et Fonctionnalités

*   **Dialogue d'Envoi d'E-mail (`dialogs/send_email_dialog.py`, `email_dialog.py`)**:
    *   **Interface de Composition**:
        *   **Destinataire(s) (À, Cc, Cci)**: Champs pour saisir ou sélectionner les adresses e-mail des destinataires. Peut s'intégrer avec le [Module Gestion des Contacts](./module_gestion_contacts.md) pour la sélection à partir du carnet d'adresses.
        *   **Expéditeur**: Généralement pré-rempli avec l'adresse e-mail de l'utilisateur connecté ou une adresse configurée pour l'entreprise ([Module Paramètres et Configuration](./module_parametres_configuration.md)), mais pourrait être sélectionnable si plusieurs comptes d'envoi sont configurés.
        *   **Sujet**: Champ pour le sujet de l'e-mail.
        *   **Corps du Message**: Éditeur de texte pour composer le message. Peut être :
            *   Un éditeur de texte simple.
            *   Un éditeur de texte enrichi (WYSIWYG léger) permettant un formatage de base (gras, italique, listes, liens).
            *   Support pour l'utilisation de modèles d'e-mails.
        *   **Pièces Jointes**:
            *   Liste des fichiers à joindre.
            *   Boutons pour ajouter des fichiers depuis le système de fichiers local.
            *   Lors de l'envoi d'un document généré par l'application (ex: facture PDF), ce document est automatiquement attaché.
    *   **Prévisualisation (Potentiel)**: Option pour prévisualiser l'e-mail (surtout si du HTML est utilisé) avant l'envoi.
    *   **Boutons d'Action**: "Envoyer", "Annuler", "Enregistrer comme Brouillon" (si supporté).

*   **Gestion des Modèles d'E-mails (`email_template_designs/`, `populate_email_templates.py`)**:
    *   **Utilisation de Modèles**: Lors de la composition d'un e-mail, l'utilisateur pourrait avoir la possibilité de sélectionner un modèle prédéfini (ex: "Rappel de paiement", "Confirmation de commande", "Invitation à un événement").
        *   Le contenu du modèle (sujet et/ou corps) est alors chargé dans le dialogue de composition.
        *   Les modèles peuvent contenir des placeholders (variables, ex: `{{NOM_CLIENT}}`, `{{NUMERO_FACTURE}}`) qui sont remplacés par des données contextuelles au moment de l'envoi ou de la sélection du modèle.
    *   **Interface de Gestion des Modèles (Potentiel, si une UI dédiée existe)**:
        *   Si l'application permet aux utilisateurs (administrateurs) de créer ou modifier les modèles d'e-mails directement depuis l'interface (plutôt que de simplement modifier les fichiers HTML dans `email_template_designs/`).
        *   Cela pourrait inclure un éditeur de texte enrichi pour les modèles HTML.
        *   Gestion des langues pour les modèles d'e-mails.
    *   Les fichiers dans `email_template_designs/` (organisés par langue) servent de base pour ces modèles. `populate_email_templates.py` pourrait les charger en base de données ou les rendre disponibles d'une autre manière pour l'application.

*   **Intégration dans les Flux de Travail**:
    *   Le dialogue d'envoi d'e-mail est typiquement invoqué depuis d'autres modules :
        *   Depuis la [Gestion des Documents](./module_gestion_documents.md) après avoir généré un devis ou une facture, avec le PDF automatiquement attaché.
        *   Depuis la [Gestion des Clients](./module_gestion_clients.md) ou la [Gestion des Contacts](./module_gestion_contacts.md) pour envoyer un message direct à un client/contact.
        *   Depuis la [Facturation et Paiements](./module_facturation_paiements.md) pour envoyer des rappels de paiement.

*   **Interaction avec `email_service.py`**:
    *   Une fois l'e-mail composé et l'action "Envoyer" cliquée, l'interface utilisateur collecte toutes les informations (destinataires, sujet, corps, pièces jointes) et les transmet à une fonction du `email_service.py` pour l'envoi effectif.

## 3. Flux de Travail Typique

### 3.1. Envoi d'une Facture par E-mail

1.  L'utilisateur génère une facture PDF dans le module de facturation.
2.  Il choisit l'option "Envoyer par e-mail".
3.  Le `SendEmailDialog` s'ouvre.
4.  **Pré-remplissage**:
    *   Le champ "À" peut être pré-rempli avec l'adresse e-mail du contact principal du client facturé.
    *   Le sujet peut être pré-rempli (ex: "Facture INV-2023-001 de VotreEntreprise").
    *   Le fichier PDF de la facture est automatiquement listé comme pièce jointe.
    *   Un modèle d'e-mail par défaut pour l'envoi de factures peut être chargé dans le corps du message.
5.  L'utilisateur peut modifier les destinataires, le sujet, et le corps du message si nécessaire. Il peut ajouter d'autres pièces jointes.
6.  L'utilisateur clique sur "Envoyer".
7.  Les données sont transmises à `email_service.py` qui tente d'envoyer l'e-mail.
8.  Une notification de succès ou d'échec est affichée à l'utilisateur.

### 3.2. Utilisation d'un Modèle d'E-mail

1.  L'utilisateur ouvre le `SendEmailDialog` (par exemple, pour un e-mail de prospection).
2.  Il choisit une option "Charger un modèle".
3.  Une liste des modèles d'e-mails disponibles s'affiche. L'utilisateur en sélectionne un.
4.  Le sujet et le corps du message dans le dialogue sont remplacés par le contenu du modèle.
5.  Si le modèle contient des placeholders, l'utilisateur peut être invité à fournir les valeurs, ou elles peuvent être remplies automatiquement si le contexte est connu (ex: si le dialogue a été ouvert depuis une fiche client).
6.  L'utilisateur complète/modifie l'e-mail et l'envoie.

## 4. Interactions avec d'Autres Modules

*   **`email_service.py` ([Module Utilitaires et Services Transverses](./module_utilitaires_services.md))**: La logique backend pour l'envoi effectif des e-mails.
*   **Gestion des Contacts**: Pour la sélection des destinataires.
*   **Gestion des Clients**: Pour pré-remplir les informations du destinataire et le contexte pour les placeholders des modèles.
*   **Gestion des Documents / Facturation / Recrutement etc.**: Comme points d'initiation pour l'envoi d'e-mails contextuels avec pièces jointes.
*   **Paramètres et Configuration**: Pour la configuration du compte SMTP d'envoi et potentiellement pour la gestion centralisée des modèles d'e-mails.
*   **Base de Données**: Peut stocker les modèles d'e-mails (via `populate_email_templates.py` et un CRUD associé si les modèles sont en base de données) et potentiellement un historique/log des e-mails envoyés.

## 5. Points d'Attention

*   **Configuration SMTP**: La facilité de configuration des paramètres SMTP est cruciale pour que la fonctionnalité soit utilisable.
*   **Gestion des Erreurs d'Envoi**: Fournir des messages d'erreur clairs si l'e-mail ne peut pas être envoyé (mauvais identifiants SMTP, adresse destinataire invalide, problème de réseau).
*   **Prévisualisation HTML**: Si les e-mails HTML sont supportés, une fonctionnalité de prévisualisation fiable est importante.
*   **Placeholders dans les Modèles**: Le système de remplacement des placeholders doit être robuste et bien documenté pour les utilisateurs qui créent/modifient les modèles.
*   **Délivrabilité**: Bien que largement hors du contrôle direct de l'application (dépendant de la réputation du serveur SMTP, etc.), s'assurer que les e-mails sont correctement formatés (MIME types, en-têtes) peut aider.
*   **Suivi des E-mails Envoyés (Historique)**: Une fonctionnalité pour voir un historique des e-mails envoyés depuis l'application (avec leur statut : envoyé, échoué, ouvert/cliqué - si des services tiers sont utilisés) serait une plus-value. Actuellement, cela ne semble pas être implémenté.
*   **Désinscription/Préférences de Communication**: Pour les e-mails en masse ou marketing (moins probable pour une application de gestion), la gestion des désinscriptions est une obligation légale.
*   **Sécurité**: Ne pas stocker les mots de passe SMTP en clair.
