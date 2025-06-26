# Fonctionnalités Clés

Ce document détaille les fonctionnalités majeures de l'application Client Document Manager, en se basant sur l'analyse du code existant et de la documentation fournie (`README.md` et dossier `cahier/`). Ces fonctionnalités couvrent à la fois l'application de bureau et, le cas échéant, leur extension ou contrepartie dans l'application mobile.

## 1. Gestion des Clients

*   **Description**: Permet de créer, stocker, organiser et gérer toutes les informations relatives aux clients.
*   **Application Desktop**:
    *   Ajout de nouveaux clients avec des informations détaillées : nom de l'entreprise, identifiant de projet, personne de contact, email, téléphone, adresse, statut (en cours, archivé, urgent), besoins spécifiques, notes.
    *   Modification des informations des clients existants.
    *   Affichage d'une liste de clients avec des capacités de recherche (par nom, ID projet, statut) et de filtrage.
    *   Vue détaillée d'un client regroupant toutes ses informations, documents associés, projets, contacts, historique d'activité.
    *   Archivage et désarchivage de clients.
    *   Liaison de personnel de l'entreprise aux clients.
    *   Gestion des transitaires, agents de transfert d'argent et transporteurs associés aux clients.
*   **Application Mobile**:
    *   Consultation de la liste des clients (informations de base).
    *   Consultation des détails d'un client spécifique (lecture seule).
    *   Sélection d'un client lors de la génération de documents.

## 2. Gestion des Produits et Catalogue

*   **Description**: Permet de gérer le catalogue des produits ou services offerts par l'entreprise.
*   **Application Desktop**:
    *   Ajout de nouveaux produits/services avec détails : nom, référence, description, prix, unité, catégorie, images, fiches techniques.
    *   Modification des informations des produits.
    *   Organisation des produits par catégories.
    *   Affichage d'une liste de produits avec recherche et filtres.
    *   Gestion des équivalences de produits.
    *   Gestion des médias (images, documents) liés aux produits.
    *   (Potentiellement) Gestion de stock interne et localisation des items.
*   **Application Mobile**:
    *   Consultation de la liste des produits (informations de base : nom, référence, prix).
    *   Sélection de produits lors de la génération de documents.

## 3. Gestion Documentaire

*   **Description**: Fonctionnalité centrale permettant de créer, organiser, stocker et retrouver des documents liés aux clients, projets, etc.
*   **Application Desktop**:
    *   **Génération de Documents à partir de Modèles**:
        *   Utilisation de modèles `.xlsx` (Excel) et `.docx` (Word) pour divers types de documents : spécifications techniques, factures proforma, contrats de vente, listes de colisage, documents de garantie, etc.
        *   Remplissage automatique des modèles avec les données du client, de l'entreprise, des produits, etc., en utilisant des placeholders (ex: `{{CLIENT_NAME}}`).
        *   Sélection de la langue du document (fr, ar, tr, en, pt, etc.), utilisant des modèles spécifiques à la langue.
    *   **Gestion des Modèles**:
        *   Organisation et gestion des fichiers modèles.
        *   Possibilité de définir des modèles par défaut pour certains types de documents.
        *   Interface pour l'ajout/modification de modèles (potentiellement via `template_dialog.py`).
    *   **Compilation PDF**:
        *   Assemblage de plusieurs documents (PDF existants ou générés) en un seul fichier PDF.
        *   Ajout automatique d'une page de garde personnalisable au PDF compilé.
    *   **Générateur de Pages de Garde (`pagedegrde.py`)**:
        *   Module dédié pour concevoir et générer des pages de garde dynamiques avec des informations contextuelles (logo, titre, client, date, etc.).
    *   **Stockage et Organisation**:
        *   Organisation des documents générés dans une structure de dossiers par client (configurable).
        *   Association de documents à des clients, projets, employés.
        *   Gestion des versions ou historique des documents (potentiel).
    *   **Éditeur Excel Intégré (`excel_editor.py`)**:
        *   Fonctionnalité basique pour visualiser et modifier des fichiers `.xlsx` directement dans l'application.
    *   **Visionneuse et Éditeur PDF (PyQt PDF Editor - `pdf_editor_pyqt/`)**:
        * Module pour visualiser et potentiellement éditer des fichiers PDF.
*   **Application Mobile**:
    *   **Génération de Documents (Simplifiée)**:
        *   Génération de certains types de documents (ex: proformas) en utilisant des modèles HTML.
        *   Le rendu HTML est effectué localement (Jinja2), puis envoyé à l'API de l'application de bureau pour conversion en PDF.
    *   Visualisation des PDF générés.
    *   Partage des documents générés (via les fonctionnalités natives du téléphone - Plyer).

## 4. Facturation et Paiements

*   **Description**: Gestion du cycle de facturation, des proformas aux factures finales et au suivi des paiements.
*   **Application Desktop**:
    *   Création et gestion de factures proforma.
    *   Conversion de proformas en factures finales.
    *   Création manuelle de factures.
    *   Personnalisation des lignes de facture (produits, services, quantités, prix, taxes).
    *   Génération des documents de facture en PDF (à partir de modèles).
    *   Suivi du statut des factures (brouillon, envoyée, payée, en retard).
    *   Enregistrement des paiements reçus et association aux factures.
    *   Gestion des avoirs (potentiel).
    *   Rapports de facturation.
*   **Application Mobile**:
    *   Génération de factures proforma (comme décrit dans la Gestion Documentaire).
    *   Consultation du statut des factures (potentiel, via API).

## 5. Gestion de Projet

*   **Description**: Outils pour planifier, suivre et gérer des projets.
*   **Application Desktop**:
    *   Création de projets liés à des clients.
    *   Définition des objectifs, portée, dates de début et de fin.
    *   Gestion des tâches, assignation aux membres de l'équipe (employés/utilisateurs).
    *   Suivi de l'avancement des tâches et des projets (statuts, pourcentage complété).
    *   Gestion des jalons (milestones).
    *   Stockage des fichiers et documents liés aux projets.
    *   Journal d'activité du projet.
    *   (Si applicable) Gestion des ordres de production et des étapes de production.
    *   Tableau de bord de gestion de projet.
*   **Application Mobile**:
    *   Consultation de la liste des projets et de leur statut (potentiel, via API).
    *   Consultation des tâches assignées (potentiel, via API).

## 6. Gestion des Utilisateurs, Rôles et Permissions

*   **Description**: Contrôle d'accès à l'application et à ses fonctionnalités.
*   **Application Desktop**:
    *   **Authentification**: Connexion sécurisée des utilisateurs (nom d'utilisateur, mot de passe).
    *   **Gestion des Utilisateurs**: Ajout, modification, suppression des comptes utilisateurs.
    *   **Gestion des Rôles**: Définition de rôles (ex: Administrateur, Commercial, Chef de Projet, Utilisateur Standard).
    *   **Gestion des Permissions**: Attribution de permissions spécifiques à chaque rôle pour contrôler l'accès aux modules et aux actions (ex: seul un admin peut ajouter des utilisateurs, seul un commercial peut créer une facture).
    *   Interface pour la gestion des utilisateurs et des rôles (`dialogs/user_dialog.py`, `security_settings_page.py`).
*   **API (pour l'application mobile)**:
    *   Authentification via token pour sécuriser l'accès aux endpoints de l'API.
    *   Les permissions définies dans l'application de bureau s'appliquent implicitement aux actions effectuées via l'API par un utilisateur authentifié.

## 7. Gestion des Contacts

*   **Description**: Gestion d'un carnet d'adresses de contacts, liés ou non à des clients.
*   **Application Desktop**:
    *   Ajout, modification, suppression de contacts (nom, email, téléphone, entreprise, rôle).
    *   Liaison de contacts à des clients.
    *   Recherche et filtrage de contacts.
    *   Synchronisation avec Google Contacts (via `contact_manager/google_people_api.py`).
*   **Application Mobile**:
    *   Consultation des contacts (potentiel, via API).

## 8. Recrutement

*   **Description**: Module pour gérer le processus de recrutement.
*   **Application Desktop**:
    *   Création et gestion des offres d'emploi.
    *   Gestion des candidatures (informations des candidats, CV, lettres de motivation).
    *   Suivi des étapes du processus de recrutement pour chaque candidat (ex: présélection, entretien 1, entretien 2, offre).
    *   Planification et suivi des entretiens.
    *   Tableau de bord du recrutement.
*   **Application Mobile**: Non applicable directement, sauf si des notifications ou des validations simples sont envisagées.

## 9. Gestion des Actifs et de l'Inventaire (Entreprise)

*   **Description**: Suivi des actifs de l'entreprise.
*   **Application Desktop**:
    *   Enregistrement des actifs de l'entreprise (matériel, licences, etc.).
    *   Suivi de l'assignation des actifs aux employés.
    *   Gestion des médias (photos, factures d'achat) liés aux actifs.
    *   (Potentiellement) Suivi de la maintenance ou de l'amortissement.

## 10. Rapports et Statistiques

*   **Description**: Fourniture d'informations consolidées pour l'aide à la décision.
*   **Application Desktop**:
    *   Tableaux de bord avec des indicateurs clés de performance (KPIs).
    *   Génération de rapports sur les ventes, les clients, les projets, la facturation, etc.
    *   Possibilité de configurer des rapports personnalisés (`db/cruds/report_configurations_crud.py`).
    *   Visualisation de statistiques (`statistics_module.py`, `statistics_page_widget.py`).
*   **Application Mobile**: Accès limité à certains rapports ou KPIs clés (potentiel, via API).

## 11. Calendrier et Gestion des Événements

*   **Description**: Module d'agenda pour gérer les événements, rendez-vous, et échéances.
*   **Application Desktop**:
    *   Affichage d'un calendrier (jour, semaine, mois).
    *   Ajout, modification, suppression d'événements.
    *   Liaison d'événements à des clients, projets, contacts.
    *   Rappels et notifications.
    *   (Potentiellement) Synchronisation avec des calendriers externes.

## 12. Gestion des E-mails (Interface Utilisateur)

*   **Description**: Facilite l'envoi d'e-mails directement depuis l'application.
*   **Application Desktop**:
    *   Interface pour composer et envoyer des e-mails (`dialogs/send_email_dialog.py`, `email_service.py`).
    *   Utilisation de modèles d'e-mails (`email_template_designs/`).
    *   Possibilité d'attacher des documents générés aux e-mails.
    *   Configuration des paramètres SMTP.
*   **Application Mobile**:
    *   Utilise Plyer pour ouvrir le client e-mail par défaut du téléphone avec des informations pré-remplies (destinataire, sujet, corps, pièce jointe).

## 13. Paramètres et Configuration

*   **Description**: Permet de personnaliser et de configurer le fonctionnement de l'application.
*   **Application Desktop**:
    *   Gestion des informations de l'entreprise (nom, adresse, logo, etc. - `company_management.py`).
    *   Configuration des chemins de dossiers (modèles, fichiers clients).
    *   Configuration des modèles par défaut.
    *   Paramètres SMTP pour l'envoi d'e-mails.
    *   Gestion des utilisateurs, rôles et permissions.
    *   Paramètres de langue et de traduction.
    *   Configuration de la base de données (implicite, via `config.py`).
    *   Paramètres de sécurité (`security_settings_page.py`).

## 14. Interaction en Langage Naturel (NLU) - Mobile

*   **Description**: Permet à l'utilisateur de l'application mobile d'effectuer certaines actions via des commandes textuelles.
*   **Application Mobile**:
    *   Interprétation de commandes simples basées sur des mots-clés et des règles (`mobile/nlu_handler.py`, `mobile/nlu_controller.py`).
    *   Traduction des commandes en actions dans l'interface utilisateur (ex: "Crée proforma pour ClientX avec ProduitY").

## 15. Intégrations Externes

*   **Application Desktop**:
    *   **Google Contacts Sync**: Synchronisation des contacts.
    *   **WooCommerce (`ecommerce_integrations/woocommerce_connector.py`)**: Intégration avec la plateforme e-commerce WooCommerce (probablement pour synchroniser produits, commandes, clients).
    *   **Botpress (`botpress_integration/`)**: Intégration avec la plateforme de chatbot Botpress.
    *   **WhatsApp (`whatsapp/`)**: Fonctionnalités liées à WhatsApp (envoi de messages, etc.).

Cette liste couvre les principales fonctionnalités identifiées. Chaque fonctionnalité peut avoir de nombreuses sous-fonctionnalités et détails d'implémentation spécifiques.
