# Module : Calendrier/Agenda (Desktop)

## 1. Objectif Principal

Le module Calendrier/Agenda de ClientDocManager vise à fournir une interface visuelle pour afficher et gérer les événements, les tâches, les échéances et autres activités importantes liées au temps. L'objectif est d'aider les utilisateurs à organiser leur emploi du temps, à suivre les dates clés et à avoir une vue d'ensemble des événements pertinents pour leur travail au sein de l'application.

## 2. Composants Clés et Fonctionnalités

*   **Widget Calendrier Principal (`calendar_module/calendar_widget.py`)**:
    *   **Affichage du Calendrier**: Vues multiples :
        *   Vue mensuelle (classique).
        *   Vue hebdomadaire.
        *   Vue journalière.
        *   Potentiellement une vue "Liste" ou "Agenda" pour les événements à venir.
    *   **Navigation**: Permettre de naviguer facilement entre les jours, les semaines et les mois.
    *   **Affichage des Événements**: Les événements, tâches, échéances sont affichés directement sur le calendrier aux dates et heures correspondantes. Des codes couleurs ou des icônes peuvent être utilisés pour distinguer les types d'événements.
    *   **Interaction avec les Événements**:
        *   Cliquer sur un événement pour voir ses détails.
        *   Possibilité de créer un nouvel événement en cliquant sur une date/heure ou via un bouton "Nouvel Événement".
        *   Modifier ou supprimer des événements existants (avec permissions).
        *   Glisser-déposer pour reprogrammer des événements (fonctionnalité avancée).

*   **Gestion des Événements (`calendar_module/api.py`, `calendar_module/cruds.py`, `calendar_module/models.py`)**:
    *   **Création/Modification d'Événements (via un dialogue dédié - non explicitement listé mais nécessaire)**:
        *   Titre de l'événement.
        *   Date et heure de début et de fin.
        *   Description détaillée.
        *   Lieu (si applicable).
        *   Participants/Invités (utilisateurs de l'application ou contacts externes).
        *   Liaison à d'autres entités de l'application (ex: un projet, un client, un candidat pour un entretien).
        *   Type d'événement (réunion, tâche, rappel, échéance, entretien, congé, etc.).
        *   Rappels/Notifications avant l'événement.
        *   Gestion de la récurrence (événements quotidiens, hebdomadaires, mensuels).
    *   **`calendar_module/cruds.py` (`important_dates_crud.py` est un exemple)**: Fonctions CRUD pour sauvegarder, lire, mettre à jour et supprimer les événements/dates importantes de la base de données. Le nom `important_dates_crud` suggère une focalisation sur des dates spécifiques, mais pourrait être étendu ou complété par un CRUD plus générique pour les événements de calendrier.
    *   **`calendar_module/models.py` (`ImportantDate` est un exemple)**: Modèle SQLAlchemy pour la table des événements/dates importantes.
    *   **`calendar_module/api.py`**: Pourrait exposer des endpoints API si le calendrier doit être accessible ou synchronisé avec des applications externes, ou utilisé par l'application mobile.

*   **Intégration d'Événements d'Autres Modules**:
    *   **Entretiens de Recrutement**: Les entretiens planifiés dans le [Module Recrutement](./module_recrutement.md) devraient apparaître dans le calendrier des participants.
    *   **Jalons et Échéances de Projets**: Les dates de début/fin des projets, les jalons et les échéances des tâches du [Module Gestion de Projet](./module_gestion_projet.md) pourraient être affichés.
    *   **Échéances de Factures**: Les dates d'échéance des factures du [Module Facturation et Paiements](./module_facturation_paiements.md) pourraient être visibles.
    *   **Congés des Employés**: Les périodes de congé validées dans un module RH pourraient bloquer des créneaux dans le calendrier des employés.

*   **Fonctionnalités Additionnelles**:
    *   **Filtres d'Affichage**: Filtrer les événements par type, par utilisateur assigné, par projet lié, etc.
    *   **Calendriers Partagés/Multi-utilisateurs**: Possibilité de voir les calendriers d'autres utilisateurs (avec permissions) ou des calendriers d'équipe/projet.
    *   **Synchronisation Externe (Potentiel)**: Synchronisation avec des calendriers externes (Google Calendar, Outlook Calendar) via CalDAV ou des APIs spécifiques. (Non visible dans la structure actuelle).

## 3. Flux de Travail Typique

### 3.1. Création d'un Nouvel Événement

1.  L'utilisateur accède au module Calendrier.
2.  Il clique sur une plage horaire ou sur un bouton "Nouvel Événement".
3.  Un dialogue de création d'événement s'ouvre.
4.  L'utilisateur remplit les détails : titre, dates/heures, description, lieu, participants, type, etc. Il peut lier l'événement à un client ou un projet.
5.  L'utilisateur valide. L'événement est enregistré en base de données via `important_dates_crud.add_important_date()` (ou un CRUD d'événements plus général).
6.  L'événement apparaît sur le calendrier. Des notifications peuvent être envoyées aux participants.

### 3.2. Consultation de l'Agenda

1.  L'utilisateur ouvre le module Calendrier.
2.  Il voit ses événements et tâches pour la période affichée (jour, semaine, mois).
3.  Il peut naviguer vers d'autres périodes.
4.  Il peut cliquer sur un événement pour en voir les détails ou le modifier.
5.  Il peut appliquer des filtres pour n'afficher que certains types d'événements (ex: uniquement les entretiens).

### 3.3. Un Entretien de Recrutement Apparaît dans le Calendrier

1.  Un recruteur planifie un entretien dans le [Module Recrutement](./module_recrutement.md).
2.  Lors de la sauvegarde de l'entretien, une entrée correspondante est automatiquement créée dans la table des événements du calendrier (ou `ImportantDate`) pour le recruteur et l'intervieweur.
3.  L'entretien apparaît dans le calendrier de ces utilisateurs.

## 4. Interactions avec d'Autres Modules

*   **Recrutement**: Les entretiens planifiés sont des événements clés du calendrier.
*   **Gestion de Projet**: Les dates de début/fin de projet, les jalons, les échéances de tâches peuvent alimenter le calendrier.
*   **Facturation et Paiements**: Les dates d'échéance des factures peuvent être des rappels dans le calendrier.
*   **Gestion des Employés (RH)**: Les demandes de congé approuvées peuvent apparaître comme des événements d'indisponibilité.
*   **Notifications**: Pour les rappels d'événements à venir.
*   **Authentification et Gestion des Utilisateurs**: Le calendrier affiche les événements pertinents pour l'utilisateur connecté. Les permissions peuvent régir la visibilité des calendriers d'autres utilisateurs.
*   **Base de Données**: Stocke tous les événements et dates importantes.

## 5. Points d'Attention

*   **Performance**: L'affichage d'un grand nombre d'événements, surtout avec des vues complexes ou des filtres, doit rester performant.
*   **Gestion des Fuseaux Horaires**: Si l'entreprise a des utilisateurs dans différents fuseaux horaires, la gestion correcte des heures d'événements est cruciale.
*   **Concurrence d'Accès**: Si plusieurs utilisateurs peuvent modifier le même calendrier partagé, la gestion de la concurrence est nécessaire.
*   **Interface Utilisateur (UI/UX)**: Un calendrier doit être intuitif et facile à lire et à manipuler.
*   **Fiabilité des Rappels**: Si des rappels sont implémentés, ils doivent être fiables.
*   **Synchronisation**: Si une synchronisation avec des calendriers externes est envisagée, la complexité augmente considérablement (gestion des conflits, authentification, mapping des données).
*   ** granularité des "Dates Importantes"**: Le modèle `ImportantDate` semble simple. Pour un module calendrier complet, un modèle `Event` plus riche (avec heures, récurrence, participants, etc.) serait typiquement nécessaire. `ImportantDate` pourrait être une simplification ou un type spécifique d'entrée de calendrier.
