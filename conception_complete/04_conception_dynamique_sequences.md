# 4. Conception Dynamique (Diagrammes de Séquence)

Ce document décrit le comportement dynamique du système en modélisant les interactions entre les différents composants lors de l'exécution de flux de travail critiques. Les diagrammes de séquence sont utilisés pour illustrer comment les objets et les acteurs collaborent pour accomplir une tâche.

## 4.1. Flux de Travail 1 : Création d'une Facture Proforma

Ce scénario décrit un **Commercial** qui utilise l'application de bureau pour créer une nouvelle facture proforma pour un client existant.

**Acteur** : Commercial
**Système** : Application de Bureau (ClientDocManager)

```mermaid
sequenceDiagram
    actor Commercial
    participant ProformaDialog as "UI: Fenêtre Proforma"
    participant ProformaLogic as "Logique Métier"
    participant ProformaCRUD as "CRUD: proformas"
    participant DB as "Base de Données"

    Commercial->>+ProformaDialog: Ouvre la création de proforma
    ProformaDialog->>Commercial: Affiche le formulaire (choix client, produits)
    Commercial->>ProformaDialog: Sélectionne un client et ajoute des produits
    Commercial->>ProformaDialog: Clique sur "Enregistrer"

    ProformaDialog->>+ProformaLogic: create_proforma(client_id, product_lines)
    ProformaLogic->>+ProformaCRUD: add_proforma_invoice(data)

    ProformaCRUD->>DB: BEGIN TRANSACTION
    ProformaCRUD->>DB: INSERT INTO proforma_invoices (...)
    ProformaCRUD->>DB: INSERT INTO proforma_invoice_items (...)
    ProformaCRUD->>DB: COMMIT TRANSACTION

    DB-->>-ProformaCRUD: return new_proforma_id
    ProformaCRUD-->>-ProformaLogic: return new_proforma_object
    ProformaLogic-->>-ProformaDialog: return success_status

    ProformaDialog-->>-Commercial: Affiche "Proforma créée avec succès"
```

**Description des interactions :**

1.  Le **Commercial** initie la création d'une proforma depuis l'interface principale.
2.  L'interface utilisateur (`ProformaDialog`) s'affiche, permettant la sélection d'un client et l'ajout de lignes de produits.
3.  Une fois le formulaire soumis, la `ProformaDialog` appelle la **Logique Métier** (une couche de service ou un contrôleur) pour orchestrer la création.
4.  La **Logique Métier** prépare les données et appelle la fonction CRUD appropriée (`ProformaCRUD`).
5.  La fonction **CRUD** est responsable des interactions avec la base de données. Elle ouvre une transaction, insère l'enregistrement principal dans la table `proforma_invoices`, insère les lignes de produits dans `proforma_invoice_items`, et valide la transaction.
6.  Le succès de l'opération est propagé en retour jusqu'à l'interface utilisateur, qui notifie le **Commercial**.

## 4.2. Flux de Travail 2 : Traitement d'une Candidature

Ce scénario décrit un **Employé RH** qui fait avancer un candidat de l'étape "Présélection" à "Entretien Technique".

**Acteur** : Employé RH
**Système** : Application de Bureau (ClientDocManager)

```mermaid
sequenceDiagram
    actor "Employé RH" as RH
    participant CandidateWidget as "UI: Fiche Candidat"
    participant RecruitmentLogic as "Logique Métier Recrutement"
    participant ProgressCRUD as "CRUD: candidate_progress"
    participant DB as "Base de Données"

    RH->>+CandidateWidget: Ouvre la fiche d'un candidat
    CandidateWidget->>DB: SELECT * FROM candidates WHERE id=...
    DB-->>CandidateWidget: Affiche les détails du candidat et son état actuel ("Présélection")

    RH->>CandidateWidget: Clique sur "Faire avancer à l'étape suivante"

    CandidateWidget->>+RecruitmentLogic: advance_candidate_stage(candidate_id, next_stage_id)
    RecruitmentLogic->>+ProgressCRUD: update_progress(candidate_id, new_stage_id, notes)

    ProgressCRUD->>DB: BEGIN TRANSACTION
    ProgressCRUD->>DB: UPDATE recruitment_candidate_progress SET status='Validé' WHERE ...
    ProgressCRUD->>DB: INSERT INTO recruitment_candidate_progress (candidate_id, step_id, status) VALUES (..., 'entretien_technique', 'En attente')
    ProgressCRUD->>DB: COMMIT TRANSACTION

    DB-->>-ProgressCRUD: return success
    ProgressCRUD-->>-RecruitmentLogic: return updated_progress_object
    RecruitmentLogic-->>-CandidateWidget: return success_status

    CandidateWidget->>CandidateWidget: Rafraîchit l'affichage de l'état
    CandidateWidget-->>-RH: Affiche le nouveau statut du candidat ("Entretien Technique")
```

**Description des interactions :**

1.  L'**Employé RH** consulte la fiche d'un candidat. L'interface charge l'état actuel du processus de recrutement pour ce candidat.
2.  L'**Employé RH** décide de faire avancer le candidat.
3.  L'interface (`CandidateWidget`) appelle la **Logique Métier** du module de recrutement.
4.  La **Logique Métier** détermine l'étape actuelle et la suivante, puis demande à la couche **CRUD** de mettre à jour la progression.
5.  La fonction **CRUD** met à jour l'enregistrement de l'étape précédente (par exemple, en le marquant comme "Validé") et insère un nouvel enregistrement pour la nouvelle étape ("En attente"). Ces opérations sont effectuées dans une transaction pour garantir la cohérence.
6.  Une fois l'opération réussie, l'interface est mise à jour pour refléter le nouveau statut du candidat.
