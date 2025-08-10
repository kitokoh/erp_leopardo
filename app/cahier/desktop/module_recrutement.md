# Module : Recrutement (Desktop)

## 1. Objectif Principal

Le module de Recrutement de ClientDocManager a pour objectif de structurer et de faciliter le processus d'embauche au sein de l'entreprise. Il permet de gérer les offres d'emploi, de suivre les candidatures, de planifier les entretiens et d'évaluer les candidats, depuis la publication d'un poste jusqu'à la décision finale.

## 2. Composants Clés et Fonctionnalités

*   **Tableau de Bord du Recrutement (`recruitment/recruitment_dashboard.py`)**:
    *   Vue d'ensemble des activités de recrutement.
    *   Affichage des offres d'emploi actives.
    *   Statistiques clés (nombre de candidats par poste, étapes en cours, etc.).
    *   Accès rapide aux différentes sections : gestion des offres, des candidats, des entretiens.

*   **Gestion des Offres d'Emploi (`recruitment/job_openings_widget.py`, `recruitment/dialogs/job_opening_dialog.py`)**:
    *   **Liste des Offres d'Emploi**: Affiche toutes les offres créées, avec leur statut (Ouvert, Clos, Brouillon).
    *   **Création/Modification d'une Offre (`JobOpeningDialog`)**:
        *   Titre du poste, description détaillée des responsabilités et des qualifications.
        *   Département, lieu de travail.
        *   Type de contrat (CDI, CDD, Stage).
        *   Date de publication, date de clôture souhaitée.
        *   Responsable du recrutement pour ce poste.
        *   Étapes du processus de recrutement associées à cette offre (`db/cruds/recruitment_steps_crud.py`).
    *   Publication de l'offre (interne ou potentiellement des liens vers des plateformes externes - non détaillé dans le code actuel).
    *   Interaction avec `db/cruds/recruitment_job_openings_crud.py`.

*   **Gestion des Candidats (`recruitment/candidates_widget.py`, `recruitment/dialogs/candidate_dialog.py`)**:
    *   **Liste des Candidats**: Affiche tous les candidats, potentiellement filtrables par offre d'emploi, statut, source.
    *   **Fiche Candidat (`CandidateDialog` pour création/édition)**:
        *   Informations personnelles (nom, prénom, coordonnées).
        *   CV, lettre de motivation et autres documents joints (interaction avec `db/cruds/employee_documents_crud.py` ou un CRUD de documents candidats spécifique).
        *   Source de la candidature (site carrière, cooptation, agence).
        *   Offre(s) d'emploi à laquelle (auxquelles) le candidat postule.
        *   Historique des interactions, notes des évaluateurs.
        *   Suivi de sa progression dans les étapes du recrutement (`db/cruds/recruitment_candidate_progress_crud.py`).
    *   Interaction avec `db/cruds/recruitment_candidates_crud.py`.

*   **Gestion des Entretiens (`recruitment/interviews_widget.py`, `recruitment/dialogs/interview_dialog.py`)**:
    *   **Planification des Entretiens**:
        *   Sélection du candidat et de l'offre d'emploi.
        *   Choix du type d'entretien (téléphonique, RH, technique, final).
        *   Date, heure, lieu (ou lien visioconférence).
        *   Participants (évaluateurs/interviewers internes).
    *   **Suivi des Entretiens**: Statut (Planifié, Réalisé, Annulé).
    *   **Feedback d'Entretien**: Saisie des commentaires et évaluations des interviewers pour chaque candidat après l'entretien.
    *   Interaction avec `db/cruds/recruitment_interviews_crud.py`.

*   **Gestion des Étapes du Processus de Recrutement**:
    *   Définition des étapes standards ou personnalisées pour chaque processus de recrutement (ex: Présélection CV, Entretien RH, Test Technique, Entretien Manager, Offre).
    *   Logique gérée via `db/cruds/recruitment_steps_crud.py`.
    *   Suivi de l'avancement de chaque candidat à travers ces étapes via `db/cruds/recruitment_candidate_progress_crud.py`.

*   **Interaction avec la Base de Données**:
    *   Un ensemble de tables et de CRUDs dédiés au recrutement :
        *   `recruitment_job_openings_crud.py`
        *   `recruitment_candidates_crud.py`
        *   `recruitment_interviews_crud.py`
        *   `recruitment_steps_crud.py`
        *   `recruitment_candidate_progress_crud.py`
    *   Modèles SQLAlchemy correspondants dans `db/models/recruitment_*.py`.

## 3. Flux de Travail Typique

### 3.1. Publication d'une Nouvelle Offre d'Emploi

1.  Un responsable RH ou un manager accède au `RecruitmentDashboard` et choisit de créer une nouvelle offre d'emploi.
2.  Le `JobOpeningDialog` s'ouvre.
3.  L'utilisateur remplit les détails du poste (titre, description, etc.) et définit les étapes du processus de recrutement pour cette offre.
4.  L'offre est sauvegardée en base de données via `recruitment_job_openings_crud.add_job_opening()`.

### 3.2. Traitement d'une Candidature

1.  Une nouvelle candidature est reçue (manuellement saisie ou importée).
2.  Un profil candidat est créé via `CandidateDialog`, lié à une ou plusieurs offres d'emploi. Le CV et autres documents sont attachés.
3.  Le candidat est initialement placé à la première étape du processus de recrutement défini pour l'offre.
4.  Les recruteurs examinent le profil. Si le candidat est retenu pour l'étape suivante :
    *   Son statut de progression est mis à jour (`recruitment_candidate_progress_crud`).
    *   Un entretien peut être planifié via `InterviewDialog`. Les détails de l'entretien sont sauvegardés (`recruitment_interviews_crud`).
5.  Après l'entretien, les évaluateurs saisissent leurs feedbacks.
6.  Le processus se répète pour les étapes suivantes jusqu'à une décision finale (embauche ou refus).

### 3.3. Planification et Suivi d'un Entretien

1.  Depuis la fiche d'un candidat ou la liste des entretiens, un recruteur planifie un nouvel entretien.
2.  `InterviewDialog` s'ouvre pour saisir la date, l'heure, les participants, le type d'entretien.
3.  Des notifications peuvent être envoyées aux participants (si le système de notification est intégré).
4.  Après l'entretien, les feedbacks sont collectés et attachés au profil du candidat et/ou à l'enregistrement de l'entretien.

## 4. Interactions avec d'Autres Modules

*   **Gestion des Employés (HR)**: Si un candidat est embauché, ses informations peuvent être transférées ou utilisées pour créer un profil employé dans le module RH (pas encore documenté, mais suggéré par `employees_crud.py`, `employee_documents_crud.py`).
*   **Calendrier/Agenda**: Les entretiens planifiés pourraient s'intégrer au module Calendrier pour les recruteurs et les interviewers.
*   **Notifications**: Pour alerter les recruteurs des nouvelles candidatures, les interviewers des entretiens planifiés, ou les candidats des changements de statut (si communication externe).
*   **Gestion Client (pour la partie documents, si applicable et centralisé)**: Les CV, lettres de motivation, et autres documents des candidats sont gérés et stockés. Si une politique de centralisation documentaire via "Gestion Client" est adoptée, ce module pourrait être utilisé. Sinon, le module Recrutement gère ses propres documents liés aux candidats.
*   **Authentification et Gestion des Utilisateurs**: Les recruteurs, managers, et interviewers sont des utilisateurs de l'application avec des permissions spécifiques pour accéder aux fonctionnalités de recrutement.
*   **Base de Données**: Stocke toutes les données relatives aux offres d'emploi, candidats, entretiens, et progression dans le processus.

## 5. Points d'Attention

*   **Confidentialité des Données Candidats (RGPD)**: Les informations des candidats sont des données personnelles et doivent être gérées conformément aux réglementations sur la protection des données.
*   **Collaboration**: Faciliter la collaboration entre les différents intervenants du processus de recrutement (recruteurs, managers, évaluateurs).
*   **Expérience Candidat**: Bien que ce soit une application interne, un processus fluide et des communications claires (même si gérées manuellement en dehors de l'outil pour l'instant) sont importants.
*   **Personnalisation du Processus**: Les entreprises ont des processus de recrutement variés. La flexibilité dans la définition des étapes est un atout.
*   **Reporting et Analyse**: Des statistiques sur l'efficacité du recrutement (durée pour pourvoir un poste, source des meilleurs candidats, taux de conversion par étape) seraient utiles.
*   **Intégration avec le site carrière/plateformes d'emploi**: Pour une automatisation accrue, l'importation automatique de candidatures depuis des sources externes serait une évolution majeure.
