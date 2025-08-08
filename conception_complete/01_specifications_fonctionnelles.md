# 1. Spécifications Fonctionnelles

Ce document décrit les fonctionnalités de l'application ClientDocManager du point de vue de l'utilisateur. Il identifie les acteurs clés et les cas d'utilisation associés à chaque grand module de l'application.

## 1.1. Acteurs du Système

Les acteurs sont les différents types d'utilisateurs qui interagissent avec le système. En se basant sur la structure des rôles et des modules, on peut identifier les acteurs suivants :

*   **Administrateur** : Super-utilisateur du système. Il a accès à toutes les fonctionnalités et est responsable de la configuration globale, de la gestion des utilisateurs et de la maintenance.
*   **Commercial** : Acteur central pour la gestion de la relation client. Il gère les fiches clients, les contacts, et l'ensemble du cycle de vente, de la proforma au paiement.
*   **Chef de Projet** : Responsable de la gestion des projets. Il planifie, exécute et suit les projets qui sont souvent liés aux clients gérés par les commerciaux.
*   **Employé RH** : Gère les processus liés aux ressources humaines, principalement le recrutement, de la publication des offres à la gestion des candidats.
*   **Utilisateur Standard** (implicite) : Un utilisateur avec des permissions de base, pouvant consulter des informations ou effectuer des tâches spécifiques sans avoir de responsabilités de gestion étendues.

## 1.2. Diagramme des Cas d'Utilisation par Module

### 1.2.1. Module : Gestion des Clients et des Ventes

Ce module est au cœur de l'application et est principalement utilisé par l'**Administrateur** et le **Commercial**.

```mermaid
graph TD
    subgraph "Module: Gestion des Clients et Ventes"
        direction LR

        actor Administrateur as Admin
        actor Commercial

        uc_gerer_clients("Gérer les fiches clients")
        uc_gerer_contacts("Gérer les contacts")
        uc_gerer_proformas("Gérer les factures proformas")
        uc_gerer_factures("Gérer les factures finales")
        uc_gerer_paiements("Enregistrer les paiements")
        uc_config_templates("Configurer les modèles de documents")

        Commercial --|> uc_gerer_clients
        Commercial --|> uc_gerer_contacts
        Commercial --|> uc_gerer_proformas
        Commercial --|> uc_gerer_factures
        Commercial --|> uc_gerer_paiements

        Admin --|> uc_gerer_clients
        Admin --|> uc_gerer_factures
        Admin --|> uc_config_templates
    end
```

**Description des cas d'utilisation :**

*   **Gérer les fiches clients** : Créer, lire, mettre à jour et archiver les informations sur les entreprises clientes.
*   **Gérer les contacts** : Gérer les personnes de contact associées à un client.
*   **Gérer les factures proformas** : Créer des devis ou des factures proformas, les envoyer aux clients et suivre leur statut (acceptée, refusée).
*   **Gérer les factures finales** : Convertir une proforma en facture, générer le document de facturation, et l'envoyer au client.
*   **Enregistrer les paiements** : Suivre les paiements reçus pour les factures émises.
*   **Configurer les modèles de documents** : L'administrateur configure les modèles (XLSX, HTML) qui seront utilisés pour générer les documents.

### 1.2.2. Module : Gestion de Projet

Ce module est utilisé par le **Chef de Projet** et l'**Administrateur**.

```mermaid
graph TD
    subgraph "Module: Gestion de Projet"
        direction LR

        actor "Chef de Projet" as CP
        actor Administrateur as Admin

        uc_gerer_projets("Gérer les projets")
        uc_assigner_client("Assigner un projet à un client")
        uc_definir_jalons("Définir les jalons")
        uc_gerer_taches("Gérer les tâches")
        uc_suivre_avancement("Suivre l'avancement")

        CP --|> uc_gerer_projets
        uc_gerer_projets --> uc_assigner_client
        uc_gerer_projets --> uc_definir_jalons
        uc_gerer_projets --> uc_gerer_taches
        CP --|> uc_suivre_avancement

        Admin --|> uc_gerer_projets
    end
```

**Description des cas d'utilisation :**

*   **Gérer les projets** : Créer, configurer et archiver des projets.
*   **Assigner un projet à un client** : Lier un projet à une fiche client existante.
*   **Définir les jalons** : Créer les étapes clés d'un projet avec des dates cibles.
*   **Gérer les tâches** : Créer et assigner des tâches spécifiques au sein d'un projet.
*   **Suivre l'avancement** : Consulter les tableaux de bord et les rapports pour suivre l'état des projets.

### 1.2.3. Module : Gestion du Recrutement

Ce module est principalement utilisé par l'**Employé RH**.

```mermaid
graph TD
    subgraph "Module: Gestion du Recrutement"
        direction LR

        actor "Employé RH" as RH

        uc_gerer_offres("Gérer les offres d'emploi")
        uc_gerer_candidats("Gérer les candidats")
        uc_planifier_entretiens("Planifier les entretiens")
        uc_suivre_processus("Suivre le processus de recrutement")

        RH --|> uc_gerer_offres
        RH --|> uc_gerer_candidats
        RH --|> uc_planifier_entretiens
        RH --|> uc_suivre_processus
    end
```

**Description des cas d'utilisation :**

*   **Gérer les offres d'emploi** : Publier de nouvelles offres d'emploi et gérer les offres existantes.
*   **Gérer les candidats** : Enregistrer les informations des candidats qui postulent aux offres.
*   **Planifier les entretiens** : Organiser les entretiens entre les candidats et les évaluateurs.
*   **Suivre le processus de recrutement** : Faire avancer un candidat à travers les différentes étapes du processus de recrutement (présélection, entretien RH, entretien technique, etc.).

### 1.2.4. Module : Administration et Configuration

Ce module est la responsabilité exclusive de l'**Administrateur**.

```mermaid
graph TD
    subgraph "Module: Administration"
        direction LR

        actor Administrateur as Admin

        uc_gerer_utilisateurs("Gérer les utilisateurs")
        uc_gerer_roles("Gérer les rôles et permissions")
        uc_gerer_parametres("Gérer les paramètres de l'application")
        uc_gerer_licences("Gérer les licences")

        Admin --|> uc_gerer_utilisateurs
        Admin --|> uc_gerer_roles
        Admin --|> uc_gerer_parametres
        Admin --|> uc_gerer_licences
    end
```

**Description des cas d'utilisation :**

*   **Gérer les utilisateurs** : Créer, modifier, et désactiver les comptes utilisateurs.
*   **Gérer les rôles et permissions** : Définir ce que chaque rôle peut faire dans l'application.
*   **Gérer les paramètres de l'application** : Configurer les options globales, comme les informations de l'entreprise, les intégrations, etc.
*   **Gérer les licences** : Gérer les licences logicielles pour l'activation du produit.
