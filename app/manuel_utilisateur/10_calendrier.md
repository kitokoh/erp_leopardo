# Chapitre 10 : Utilisation du Calendrier/Agenda

Le module Calendrier (ou Agenda) de ClientDocManager vous aide à visualiser et à organiser votre temps, à suivre les échéances importantes, les rendez-vous, et les événements liés à votre travail au sein de l'application.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 10.1. Accéder au Module Calendrier

1.  Repérez le **Volet de Navigation Principal**.
2.  Cliquez sur l'icône ou le libellé **Calendrier** ou **Agenda**.
3.  La **Zone d'Affichage Principale** se mettra à jour pour afficher votre calendrier.

## 10.2. L'Interface du Calendrier (`calendar_widget.py`)

L'interface du module Calendrier offre généralement plusieurs vues et fonctionnalités :

*   **Affichage Principal du Calendrier**:
    *   **Vues Disponibles**: Vous pouvez souvent basculer entre différentes vues :
        *   **Vue Mois**: Affiche le mois entier avec les événements résumés sur chaque jour.
        *   **Vue Semaine**: Affiche les jours de la semaine sélectionnée avec les plages horaires.
        *   **Vue Jour**: Affiche les plages horaires pour la journée sélectionnée.
        *   **Vue Liste/Agenda**: Affiche une liste chronologique des événements à venir.
    *   **Navigation Temporelle**: Des flèches ou des boutons vous permettent de passer au jour/semaine/mois précédent ou suivant. Un bouton "Aujourd'hui" vous ramène à la date actuelle.
    *   **Affichage des Événements**: Les événements sont représentés par des blocs colorés ou des libellés sur le calendrier. La couleur peut indiquer le type d'événement ou son statut.

*   **Barre d'Outils ou Panneau d'Actions**:
    *   **Nouvel Événement**: Bouton pour créer un nouvel événement manuellement.
    *   **Filtres**: Options pour filtrer les événements affichés (par type, par calendrier partagé, par statut, etc.).
    *   **Paramètres du Calendrier** (Potentiel): Options pour personnaliser l'affichage, les rappels par défaut, etc.

## 10.3. Créer un Nouvel Événement

1.  **Méthode 1 : Cliquer sur le Calendrier**
    *   Dans la vue Jour ou Semaine, cliquez directement sur la plage horaire où vous souhaitez ajouter l'événement.
    *   Dans la vue Mois, cliquez sur le jour souhaité.
    *   Un dialogue de création rapide ou complet peut s'ouvrir.
2.  **Méthode 2 : Utiliser le Bouton "Nouvel Événement"**
    *   Cliquez sur le bouton **Nouvel Événement**.
    *   Le dialogue de création d'événement s'ouvrira.
3.  **Remplir les Détails de l'Événement**:
    *   `Titre de l'événement`: Un nom clair pour l'événement (ex: "Réunion équipe projet X", "Appel de suivi client Y").
    *   `Date de début` et `Heure de début`.
    *   `Date de fin` et `Heure de fin` (ou `Durée`).
    *   `Événement sur toute la journée`: Cochez si l'événement dure toute la journée sans heure précise.
    *   `Description/Ordre du jour`: Plus de détails sur l'événement.
    *   `Lieu`: (Ex: Salle de réunion A, lien visioconférence).
    *   `Participants/Invités`: Ajoutez d'autres utilisateurs de ClientDocManager ou des contacts externes (par leur adresse e-mail).
    *   `Type d'événement`: (Ex: Réunion, Appel, Tâche, Rappel, Échéance, Personnel). Cela peut influencer la couleur de l'événement sur le calendrier.
    *   `Lier à...`: Option pour associer cet événement à un Client, un Projet, une Offre de recrutement (pour un entretien), etc.
    *   `Rappel`: Configurez un ou plusieurs rappels (ex: 15 minutes avant, 1 jour avant) qui peuvent générer une notification dans l'application.
    *   `Récurrence`: Si l'événement se répète (quotidien, hebdomadaire, mensuel, annuel), configurez les règles de récurrence.
4.  Cliquez sur **Enregistrer** ou **OK**. L'événement sera ajouté à votre calendrier et, si des participants ont été ajoutés, ils pourraient recevoir une notification ou une invitation.

## 10.4. Visualiser et Modifier un Événement

*   **Visualiser**: Cliquez simplement sur un événement dans le calendrier. Une info-bulle ou un panneau de détails peut s'afficher avec les informations clés. Double-cliquer ouvre souvent le dialogue de modification.
*   **Modifier**:
    1.  Double-cliquez sur l'événement ou sélectionnez-le et cliquez sur un bouton **Modifier**.
    2.  Le dialogue d'événement s'ouvrira avec les informations actuelles.
    3.  Apportez vos modifications.
    4.  Cliquez sur **Enregistrer**. Si l'événement a des participants, ils peuvent être notifiés des changements.
*   **Reprogrammer par Glisser-Déposer**: Dans certaines vues (Semaine, Jour), vous pourriez être capable de cliquer et faire glisser un événement vers un nouveau créneau horaire ou un autre jour pour le reprogrammer rapidement.
*   **Supprimer**: Sélectionnez l'événement et cliquez sur **Supprimer** (ou via un menu contextuel). Confirmez la suppression.

## 10.5. Intégration avec d'Autres Modules

Le calendrier est particulièrement utile car il peut se remplir automatiquement avec des informations provenant d'autres modules :

*   **Entretiens de Recrutement**: Lorsqu'un entretien est planifié dans le [Module Recrutement](./09_recrutement.md), il apparaît automatiquement dans le calendrier des participants.
*   **Jalons et Échéances de Projets**: Les dates importantes (jalons, échéances de tâches critiques) du [Module Gestion de Projets](./07_gestion_projets.md) peuvent être affichées.
*   **Échéances de Factures**: Les dates d'échéance des factures du [Module Facturation et Suivi des Paiements](./06_facturation_paiements.md) peuvent apparaître comme des rappels.
*   **Congés et Absences (Module RH potentiel)**: Si un module RH gère les congés, les absences approuvées des collègues (ou les vôtres) peuvent être visibles.

## 10.6. Gérer les "Dates Importantes"

Le système peut aussi gérer des "Dates Importantes" (`ImportantDate`) qui sont plus simples que des événements de calendrier complets (sans heure de début/fin spécifique, ni participants). Celles-ci peuvent servir de rappels généraux ou marquer des événements sur une journée entière. La création et la gestion se font de manière similaire via un dialogue dédié.

## 10.7. Filtres et Affichages Personnalisés

*   Utilisez les options de **filtre** si disponibles pour ne voir que certains types d'événements (ex: uniquement vos réunions, ou uniquement les échéances de projet).
*   Si des **calendriers partagés** sont supportés (calendrier d'équipe, calendrier d'un collègue), vous pourrez les sélectionner pour les superposer ou les afficher à côté du vôtre.

Le calendrier est un outil personnel et collaboratif qui vous aide à rester organisé et à ne manquer aucune échéance importante.
