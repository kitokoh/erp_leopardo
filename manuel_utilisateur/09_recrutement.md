# Chapitre 9 : Module Recrutement

Si votre entreprise utilise ClientDocManager pour gérer ses processus d'embauche, le module Recrutement vous offre des outils pour publier des offres d'emploi, suivre les candidatures, planifier des entretiens et gérer le pipeline de recrutement.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 9.1. Accéder au Module Recrutement

1.  Repérez le **Volet de Navigation Principal**.
2.  Cliquez sur l'icône ou le libellé **Recrutement**, **Carrières**, ou un terme similaire.
3.  La **Zone d'Affichage Principale** se mettra à jour, affichant généralement un tableau de bord du recrutement.

## 9.2. Le Tableau de Bord du Recrutement (`RecruitmentDashboard`)

Le tableau de bord est votre point d'entrée pour les activités de recrutement. Il peut afficher :

*   Une liste des **Offres d'Emploi Actives**.
*   Des statistiques rapides (ex: nombre total de candidats, entretiens à venir).
*   Des raccourcis pour accéder aux sections :
    *   Gestion des Offres d'Emploi
    *   Gestion des Candidats
    *   Gestion des Entretiens

## 9.3. Gestion des Offres d'Emploi

### 9.3.1. Créer une Nouvelle Offre d'Emploi

1.  Depuis le tableau de bord ou la section "Offres d'Emploi", cliquez sur **Nouvelle Offre d'Emploi**.
2.  Le dialogue **Créer/Modifier une Offre d'Emploi** (`JobOpeningDialog`) s'ouvre.
3.  Remplissez les détails de l'offre :
    *   `Titre du poste` (ex: "Développeur Python Senior").
    *   `Description`: Détaillez les responsabilités, les qualifications requises, les avantages, etc.
    *   `Département`, `Lieu de travail`.
    *   `Type de contrat` (CDI, CDD, Stage, etc.).
    *   `Date de publication` et `Date de clôture` souhaitée pour les candidatures.
    *   `Responsable du recrutement`: Sélectionnez l'utilisateur en charge de ce recrutement.
    *   `Étapes du processus`: Définissez ou sélectionnez les étapes par lesquelles les candidats passeront (ex: Présélection CV, Entretien RH, Test Technique, Entretien Final).
4.  Cliquez sur **Enregistrer**. L'offre est créée (souvent avec un statut "Brouillon" ou "Ouvert").

### 9.3.2. Gérer les Offres Existantes

*   Dans la liste des offres (`JobOpeningsWidget`), vous pouvez :
    *   **Visualiser** les détails d'une offre.
    *   **Modifier** une offre (surtout si elle est encore en brouillon ou si des ajustements sont nécessaires).
    *   **Changer le statut** (ex: passer de "Ouvert" à "Clos" une fois le poste pourvu).
    *   **Supprimer** une offre (si aucune candidature n'y est liée ou si elle a été créée par erreur).
    *   **Voir les candidats** qui ont postulé à cette offre.

## 9.4. Gestion des Candidats

### 9.4.1. Ajouter un Nouveau Candidat

Les candidats peuvent être ajoutés manuellement ou provenir d'autres sources (import, site carrière - si intégré).

1.  Depuis la section "Candidats" ou directement depuis une offre d'emploi, cliquez sur **Ajouter Candidat**.
2.  Le dialogue **Créer/Modifier un Candidat** (`CandidateDialog`) s'ouvre.
3.  Remplissez les informations du candidat :
    *   `Nom`, `Prénom`.
    *   `Coordonnées`: E-mail, téléphone.
    *   `Source de la candidature`: Comment avez-vous trouvé ce candidat (site web, cooptation, etc.)?
    *   `Offre(s) d'emploi postulée(s)`: Liez le candidat à une ou plusieurs offres ouvertes.
    *   **Pièces Jointes**: Téléchargez le CV, la lettre de motivation, et tout autre document pertinent.
4.  Cliquez sur **Enregistrer**.

### 9.4.2. Suivre la Progression d'un Candidat

1.  Ouvrez la fiche d'un candidat ou visualisez la liste des candidats pour une offre spécifique.
2.  Vous verrez à quelle **étape du processus de recrutement** le candidat se trouve actuellement.
3.  Pour faire avancer un candidat :
    *   Sélectionnez le candidat.
    *   Choisissez une action comme **Passer à l'étape suivante**, **Planifier un entretien**, ou **Rejeter la candidature**.
    *   Vous pourriez être invité à ajouter des notes ou des commentaires justifiant cette action.
4.  L'historique de la progression du candidat est conservé.

## 9.5. Gestion des Entretiens

### 9.5.1. Planifier un Entretien

1.  Depuis la fiche d'un candidat qui a atteint l'étape appropriée, cliquez sur **Planifier un Entretien**.
2.  Le dialogue **Planifier/Modifier un Entretien** (`InterviewDialog`) s'ouvre.
3.  Remplissez les détails :
    *   `Candidat` et `Offre d'emploi` (souvent pré-remplis).
    *   `Type d'entretien` (Téléphonique, Entretien RH, Test Technique, Entretien avec le manager).
    *   `Date` et `Heure` de l'entretien.
    *   `Lieu` (ou lien pour une visioconférence).
    *   `Participants/Évaluateurs`: Sélectionnez les utilisateurs de ClientDocManager qui mèneront l'entretien.
4.  Cliquez sur **Enregistrer**. L'entretien est planifié.
    *   Cet événement peut automatiquement apparaître dans le [Module Calendrier](./10_calendrier.md) des participants.
    *   Des notifications par e-mail peuvent être envoyées (si configuré).

### 9.5.2. Enregistrer le Feedback d'Entretien

1.  Après un entretien, l'évaluateur (ou le recruteur) ouvre la fiche de l'entretien réalisé.
2.  Il y a une section pour saisir le **feedback**, les **notes**, et une **évaluation** (ex: Positif, Neutre, Négatif ; ou une note chiffrée).
3.  Ce feedback est crucial pour la décision finale.

## 9.6. Prendre une Décision

Après que le candidat a passé toutes les étapes nécessaires :
1.  L'équipe de recrutement examine tous les feedbacks et informations.
2.  Une décision est prise : **Embaucher** ou **Ne pas embaucher**.
3.  Le statut du candidat pour l'offre est mis à jour.
    *   Si embauché, le candidat peut être transféré vers un processus d'intégration RH (potentiellement lié au module Employés).
    *   Si non retenu, une communication (souvent par e-mail) peut être envoyée.

Le module Recrutement vous aide à garder une trace organisée de tous les aspects de vos processus d'embauche, améliorant l'efficacité et la collaboration entre les recruteurs et les managers.
