# Chapitre 7 : Gestion de Projets

Si votre activité implique la réalisation de projets pour vos clients ou en interne, le module de Gestion de Projets de ClientDocManager peut vous aider à les planifier, les suivre et à centraliser les informations associées.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 7.1. Accéder au Module de Gestion de Projets

1.  Repérez le **Volet de Navigation Principal**.
2.  Cliquez sur l'icône ou le libellé **Projets** ou **Gestion de Projets**.
3.  La **Zone d'Affichage Principale** se mettra à jour, affichant généralement un tableau de bord ou une liste de vos projets.

## 7.2. Le Tableau de Bord des Projets (`project_management/dashboard.py`)

Lorsque vous entrez dans le module, vous voyez souvent un tableau de bord qui peut inclure :

*   **Liste des Projets**: Un tableau avec des colonnes comme : Nom du Projet, Client Associé, Chef de Projet, Date de Début, Date de Fin Prévue, Statut (Planifié, En Cours, Terminé, En Retard, Annulé), Pourcentage d'Achèvement.
*   **Filtres et Recherche**: Options pour filtrer les projets (par statut, client, etc.) et un champ de recherche.
*   **Indicateurs Clés (KPIs)**: Potentiellement des graphiques ou des chiffres clés sur le nombre de projets par statut, le respect des délais, etc.
*   **Actions Rapides**: Bouton pour **Créer un Nouveau Projet**.

## 7.3. Créer un Nouveau Projet

1.  Depuis le tableau de bord des projets, cliquez sur **Créer un Nouveau Projet**.
2.  Un dialogue de création de projet s'ouvrira. Remplissez les informations :
    *   `Nom du Projet`: Un titre clair et descriptif.
    *   `Description`: Objectifs, portée, et détails importants du projet.
    *   `Client Associé`: Sélectionnez le client pour lequel ce projet est réalisé (depuis votre liste de clients - voir [Chapitre 3](./03_gestion_clients.md)).
    *   `Chef de Projet`: Assignez un utilisateur de ClientDocManager comme responsable du projet.
    *   `Date de Début` et `Date de Fin Prévue`.
    *   `Statut Initial`: (Ex: Planifié).
    *   `Budget Alloué` (si applicable).
3.  Cliquez sur **OK** ou **Enregistrer**. Le projet est créé et apparaît dans la liste.

## 7.4. Consulter et Gérer les Détails d'un Projet

Une fois un projet créé, vous pouvez accéder à sa vue détaillée pour une gestion plus fine.

1.  Sélectionnez un projet dans la liste du tableau de bord.
2.  Cliquez sur **Ouvrir**, **Détails**, ou double-cliquez sur le projet.
3.  La vue détaillée du projet peut comporter plusieurs onglets ou sections :

    *   **Informations Générales**: Rappel des informations saisies à la création (nom, client, dates, statut), que vous pouvez souvent **Modifier**.
    *   **Tâches ou Phases**:
        *   Décomposez votre projet en tâches ou phases plus petites.
        *   Pour chaque tâche : nom, description, personne assignée, date d'échéance, statut (À faire, En cours, Terminé).
        *   Options pour **Ajouter une tâche**, **Modifier**, **Supprimer**.
    *   **Jalons (`Milestones`)**:
        *   Définissez les étapes clés ou les livrables importants du projet avec des dates cibles.
        *   Marquez les jalons comme atteints.
        *   Options pour **Ajouter un jalon**, **Modifier**, **Supprimer**.
    *   **Documents du Projet**:
        *   Téléchargez et organisez tous les fichiers relatifs au projet (cahier des charges, plans, comptes rendus, livrables, etc.).
        *   Option pour **Ajouter un document** (télécharger un fichier). Si le document est déjà dans le système via la **Gestion Client**, vous pourrez le lier.
        *   La création de documents spécifiques au projet (comme des rapports ou des pages de garde) utilisera les fonctionnalités de génération documentaire désormais intégrées à la **Gestion Client**, en sélectionnant le contexte du projet.
        *   Vous pourriez aussi y trouver un outil pour créer des **Pages de Garde** spécifiques aux documents de ce projet, utilisant les modèles de la **Gestion Client**.
    *   **Membres de l'Équipe**: Listez ou assignez les utilisateurs qui participent au projet (en plus du chef de projet).
    *   **Journal d'Activité (`Project Logs`)**: Un historique des actions importantes réalisées sur le projet (changements de statut, ajout de documents, tâches complétées).
    *   **Produits/Livrables Associés**: Si le projet implique la livraison de produits spécifiques de votre catalogue, vous pouvez les lier ici.
    *   **Ordres de Production** (si votre projet implique une fabrication) :
        *   Création et suivi des ordres de production, avec leurs étapes.

## 7.5. Mettre à Jour l'Avancement

Au fur et à mesure que le projet progresse :

*   **Mettez à jour le statut des tâches** (ex: passez une tâche de "En cours" à "Terminé").
*   **Marquez les jalons comme atteints**.
*   **Modifiez le statut général du projet** (ex: de "En Cours" à "Terminé").
*   La barre de progression du projet (si affichée) devrait se mettre à jour en conséquence.

## 7.6. Gérer les Statuts de Projet/Tâche

L'application peut proposer une interface pour gérer les différents types de statuts utilisables pour les projets ou les tâches (via `StatusManagementDialog`). Cela permet de personnaliser les workflows selon les besoins de votre entreprise.

## 7.7. Notifications de Projet

Le système peut générer des notifications (voir [Module Notifications](../cahier/desktop/module_utilitaires_services.md) section 2.2) pour :
*   Vous rappeler des échéances de tâches ou de jalons.
*   Vous informer de l'assignation d'une nouvelle tâche.
*   Signaler des retards.

La gestion de projet est un outil puissant pour organiser le travail complexe. Prenez le temps de bien structurer vos projets, de définir clairement les tâches et les responsabilités pour une meilleure efficacité.
