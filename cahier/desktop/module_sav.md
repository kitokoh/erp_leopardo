# Module : Support Après-Vente (SAV) (Desktop)

## 1. Objectif Principal

Le module de Support Après-Vente (SAV) de ClientDocManager a pour objectif de fournir des outils pour enregistrer, suivre et gérer les demandes de support, les réclamations, et les problèmes rencontrés par les clients après l'achat d'un produit ou service. Il vise à améliorer la satisfaction client en assurant un traitement efficace et organisé des tickets de SAV.

## 2. Composants Clés et Fonctionnalités (Partiellement Inférence)

La présence du dossier `sav/` et de `sav/ticket_dialog.py` suggère les fonctionnalités suivantes. D'autres composants (comme un widget principal de gestion des tickets) sont inférés comme étant nécessaires pour un module SAV complet.

*   **Widget de Gestion des Tickets SAV (Interface Principale - Supposée)**:
    *   **Affichage de la Liste des Tickets**: Tableau ou liste présentant les tickets de SAV avec des informations clés (Numéro de Ticket, Client, Produit/Service concerné, Sujet, Date de Création, Statut, Priorité, Agent Assigné).
    *   **Fonctionnalités de Tri et de Filtrage**: Permettre de trier par différentes colonnes et de filtrer les tickets (par statut, client, agent, priorité, etc.).
    *   **Recherche Rapide**: Pour trouver un ticket spécifique.
    *   **Actions sur les Tickets**:
        *   Créer un nouveau ticket.
        *   Ouvrir et visualiser les détails d'un ticket.
        *   Assigner un ticket à un agent de support.
        *   Changer le statut d'un ticket (Ouvert, En cours, En attente client, Résolu, Clos).
        *   Changer la priorité d'un ticket.
        *   Ajouter des réponses, des notes internes, ou des actions effectuées.

*   **Dialogue de Gestion de Ticket (`sav/ticket_dialog.py`)**:
    *   Interface modale pour la création et la modification/consultation d'un ticket SAV.
    *   **Champs à la Création**:
        *   Client concerné (liaison avec le [Module Gestion des Clients](./module_gestion_clients.md)).
        *   Produit/Service concerné (liaison avec le [Module Gestion des Produits](./module_gestion_produits.md)).
        *   Sujet/Titre du problème.
        *   Description détaillée du problème fournie par le client ou l'agent.
        *   Canal de réception (Téléphone, E-mail, Portail client - si applicable).
        *   Priorité initiale.
        *   Pièces jointes (captures d'écran, logs, etc.).
    *   **Champs en Consultation/Modification**:
        *   Historique des échanges et des actions (journal du ticket).
        *   Possibilité d'ajouter une nouvelle réponse ou une note interne.
        *   Modification du statut, de la priorité, de l'agent assigné.
        *   Solution apportée (si résolu).

*   **Gestion des Statuts et Priorités des Tickets**:
    *   Définition de statuts clairs pour suivre le cycle de vie d'un ticket.
    *   Niveaux de priorité pour aider à organiser le traitement des demandes.

*   **Assignation des Tickets**:
    *   Possibilité d'assigner manuellement un ticket à un agent de support spécifique (utilisateur de l'application).
    *   Potentiellement, des règles d'assignation automatique basées sur le type de produit, la catégorie de problème, etc. (fonctionnalité avancée).

*   **Base de Connaissances (Potentiel)**:
    *   Une section où les solutions aux problèmes fréquents sont documentées, accessible aux agents de support pour accélérer la résolution.
    *   Possibilité de créer un article de base de connaissances à partir d'un ticket résolu.

*   **Notifications**:
    *   Notifications aux agents lors de l'assignation d'un nouveau ticket ou de la mise à jour d'un ticket existant.
    *   Notifications aux clients (par e-mail via le [Module Gestion des E-mails](./module_gestion_emails_ui.md)) lors de la création du ticket, des mises à jour importantes, ou de sa résolution (ex: `email_template_designs/sav_ticket_opened_fr.html`, `sav_ticket_resolved_fr.html`).

*   **Interaction avec la Base de Données**:
    *   **`db/cruds/sav_tickets_crud.py`** (Nom supposé, basé sur la logique d'autres modules) : Fonctions CRUD pour les tickets SAV.
    *   **`db/cruds/sav_ticket_history_crud.py`** (Nom supposé) : Pour l'historique des actions et des communications sur un ticket.
    *   **`db/models/sav_ticket.py`**, **`db/models/sav_ticket_history.py`** (Noms supposés) : Définitions SQLAlchemy des tables correspondantes.

## 3. Flux de Travail Typique

### 3.1. Création d'un Nouveau Ticket SAV

1.  Un client contacte le support (par téléphone, e-mail) ou un agent identifie un problème.
2.  L'agent de support clique sur "Créer Ticket" dans l'interface de gestion des tickets SAV.
3.  Le `TicketDialog` s'ouvre.
4.  L'agent sélectionne le client, le produit concerné (si applicable), saisit le sujet et la description du problème, la source, et la priorité. Il peut joindre des fichiers.
5.  Le ticket est enregistré en base de données avec un statut "Ouvert" et un numéro unique.
6.  Le ticket apparaît dans la liste des tickets. Une notification peut être envoyée au client pour confirmer la création.
7.  Le ticket peut être assigné (ou s'auto-assigner) à un agent.

### 3.2. Traitement d'un Ticket SAV

1.  Un agent de support prend en charge un ticket assigné (ou non assigné).
2.  Il consulte les détails du ticket dans `TicketDialog` (en mode consultation/édition).
3.  Il peut ajouter des notes internes sur ses investigations.
4.  Il peut communiquer avec le client (par e-mail ou autre moyen, et consigner l'échange dans le ticket).
5.  Il met à jour le statut du ticket (ex: "En cours", "En attente client").
6.  Une fois le problème résolu, l'agent documente la solution, met le statut à "Résolu", et peut notifier le client.
7.  Après confirmation du client ou une période définie, le ticket peut être "Clos".

## 4. Interactions avec d'Autres Modules

*   **Gestion des Clients**: Chaque ticket est généralement lié à un client. Le module SAV accède aux informations du client.
*   **Gestion des Produits**: Les tickets peuvent concerner des produits spécifiques. Le module SAV accède aux informations des produits.
*   **Gestion des Employés (RH)**: Les agents de support sont des employés/utilisateurs de l'application.
*   **Gestion des E-mails (Interface Utilisateur)**: Pour envoyer des notifications et des réponses aux clients concernant leurs tickets. Les modèles d'e-mails spécifiques au SAV (`email_template_designs/sav_*.html`) sont utilisés.
*   **Notifications**: Pour les alertes internes et les communications externes.
*   **Base de Données**: Stocke toutes les informations relatives aux tickets, leur historique, et les liaisons avec les clients/produits.
*   **Base de Connaissances (Potentiel)**: Les solutions des tickets peuvent alimenter la base de connaissances.

## 5. Points d'Attention

*   **Définition Claire des Processus**: Avoir des processus SAV bien définis (escalade, SLA - Service Level Agreements) que l'outil peut supporter.
*   **Communication Client**: Assurer une communication claire et régulière avec le client sur l'état de son ticket.
*   **Historique Complet**: Conserver un historique détaillé de toutes les actions et communications pour chaque ticket est crucial pour le suivi et la résolution.
*   **Reporting SAV**: Des rapports sur le volume de tickets, les temps de résolution, la satisfaction client, les problèmes récurrents par produit, sont importants pour améliorer le service et les produits.
*   **Intégration des Canaux**: Si le support est multicanal (téléphone, e-mail, portail), l'idéal est de centraliser toutes les interactions dans le ticket.
*   **Formation des Agents**: Les agents de support doivent être formés à l'utilisation efficace du module.
*   **Priorisation et Escalade**: Mécanismes pour gérer la priorisation des tickets et les procédures d'escalade en cas de problèmes complexes ou urgents.
