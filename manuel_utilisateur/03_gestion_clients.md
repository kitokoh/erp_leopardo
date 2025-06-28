# Chapitre 3 : Gestion des Clients

La gestion efficace de vos clients est fondamentale. Ce chapitre vous explique comment utiliser le module "Clients" de ClientDocManager pour créer, rechercher, visualiser et modifier les fiches de vos clients.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 3.1. Accéder au Module Clients

Pour accéder au module de gestion des clients :

1.  Repérez le **Volet de Navigation Principal** (généralement sur le côté gauche de la fenêtre principale).
2.  Cliquez sur l'icône ou le libellé **Clients**.
3.  La **Zone d'Affichage Principale** se mettra à jour pour afficher la liste de vos clients.

## 3.2. L'Interface du Module Clients

L'interface du module Clients se compose généralement des éléments suivants :

*   **Liste des Clients**:
    *   Un tableau affichant vos clients. Chaque ligne représente un client et chaque colonne une information clé (ex: Nom de la société, Nom du contact principal, Téléphone, E-mail, Statut, Commercial assigné).
    *   **Barre de recherche**: Un champ au-dessus de la liste pour rechercher rapidement un client par son nom, sa société, etc.
    *   **Options de tri**: Vous pouvez souvent trier la liste en cliquant sur les en-têtes de colonnes (ex: cliquer sur "Nom de la société" pour trier alphabétiquement).
    *   **Options de filtrage**: Des listes déroulantes ou des boutons peuvent être disponibles pour filtrer les clients (ex: afficher uniquement les clients "Actifs", ou ceux assignés à un commercial spécifique).
*   **Barre d'Outils Spécifique aux Clients**:
    *   Des boutons pour les actions courantes :
        *   **Nouveau Client**: Pour créer une nouvelle fiche client.
        *   **Modifier Client**: Pour modifier la fiche du client sélectionné.
        *   **Supprimer Client**: Pour supprimer le client sélectionné (une confirmation sera demandée).
        *   **Visualiser Détails**: Pour ouvrir une vue plus détaillée du client sélectionné.
*   **Panneau de Détails (Optionnel)**:
    *   Certaines interfaces peuvent afficher un panneau de détails rapides sur le côté ou en bas lorsque vous sélectionnez un client dans la liste, sans avoir à ouvrir une nouvelle fenêtre.

## 3.3. Créer un Nouveau Client

1.  Dans le module Clients, cliquez sur le bouton **Nouveau Client** (ou utilisez l'option de menu **Fichier > Nouveau > Client**).
2.  La fenêtre (dialogue) **Ajouter un Nouveau Client** s'ouvrira.
3.  Remplissez les informations demandées. Les champs courants incluent :
    *   **Informations sur la société**: Nom de la société, forme juridique, SIRET/Numéro de TVA.
    *   **Adresse principale**: Adresse, code postal, ville, pays. (Il peut y avoir des sections pour des adresses multiples comme l'adresse de facturation et de livraison).
    *   **Informations de contact générales**: Téléphone principal de la société, e-mail générique, site web.
    *   **Contact principal**: Nom, prénom, fonction, e-mail direct, téléphone direct du contact principal chez ce client. (Des options pour ajouter plusieurs contacts peuvent exister).
    *   **Statut du client**: (Ex: Prospect, Actif, Inactif, Ancien client).
    *   **Commercial assigné**: Sélectionnez l'utilisateur de ClientDocManager responsable de ce client.
    *   **Conditions de paiement par défaut**, informations bancaires (RIB/IBAN).
    *   **Notes**: Un espace pour ajouter des commentaires ou informations spécifiques sur ce client.
4.  Certains champs peuvent être obligatoires (souvent indiqués par un astérisque \*).
5.  Une fois toutes les informations saisies, cliquez sur **OK** ou **Enregistrer**.
6.  Si les informations sont valides, le nouveau client sera ajouté à votre base de données et apparaîtra dans la liste des clients. Cliquez sur **Annuler** pour fermer le dialogue sans enregistrer.

## 3.4. Rechercher un Client

Utilisez le champ **Recherche** situé généralement au-dessus de la liste des clients.
1.  Cliquez dans le champ de recherche.
2.  Commencez à taper le nom de la société, le nom d'un contact, un numéro de téléphone, une adresse e-mail, ou toute autre information que vous pensez pouvoir identifier le client.
3.  La liste des clients se filtrera dynamiquement pour n'afficher que les résultats correspondants à votre recherche.

## 3.5. Visualiser et Modifier les Informations d'un Client

1.  **Sélectionnez le client** dans la liste en cliquant une fois sur sa ligne.
2.  **Pour visualiser les détails complets**:
    *   Cliquez sur le bouton **Visualiser Détails** (s'il existe).
    *   Ou double-cliquez sur la ligne du client.
    *   Cela peut ouvrir une nouvelle fenêtre ou un onglet affichant toutes les informations du client, y compris les contacts multiples, l'historique des documents, les projets liés, etc.
3.  **Pour modifier les informations**:
    *   Avec le client sélectionné, cliquez sur le bouton **Modifier Client**.
    *   La fenêtre **Modifier Client** s'ouvrira, pré-remplie avec les informations actuelles du client. Elle ressemble généralement à la fenêtre d'ajout de nouveau client.
    *   Apportez les modifications souhaitées aux champs.
    *   Cliquez sur **OK** ou **Enregistrer** pour sauvegarder vos modifications.

## 3.6. Supprimer un Client

**Attention**: La suppression d'un client est généralement une action irréversible ou difficilement réversible (sauf si l'application gère un système d'archivage). Assurez-vous de vouloir réellement supprimer le client.

1.  **Sélectionnez le client** que vous souhaitez supprimer dans la liste.
2.  Cliquez sur le bouton **Supprimer Client**.
3.  Une **boîte de dialogue de confirmation** apparaîtra, vous demandant si vous êtes sûr de vouloir supprimer ce client.
4.  Cliquez sur **Oui** ou **Confirmer** pour procéder à la suppression. Cliquez sur **Non** ou **Annuler** si vous avez changé d'avis.
5.  Si le client a des documents, factures, ou projets liés, l'application peut vous empêcher de le supprimer directement ou vous proposer de l'archiver à la place.

## 3.7. Gérer les Contacts d'un Client

Souvent, une entreprise cliente a plusieurs personnes de contact.
*   Lorsque vous êtes dans la fiche détaillée d'un client ou dans le dialogue de modification, cherchez une section ou un onglet "Contacts".
*   Vous devriez y trouver des options pour **Ajouter un nouveau contact** spécifique à ce client, **Modifier** un contact existant, ou le **Supprimer**.
*   Pour plus de détails sur la gestion globale des contacts (qui peuvent aussi être indépendants d'un client), référez-vous au chapitre [Gestion des Contacts](./08_gestion_contacts.md).

## 3.8. Consulter les Documents et Projets Liés

Depuis la fiche détaillée d'un client, vous aurez généralement accès à :
*   Un onglet ou une section listant tous les **documents** (devis, factures, contrats, etc.) qui ont été créés pour ce client.
*   Un onglet ou une section listant tous les **projets** qui sont associés à ce client.

Cela vous permet d'avoir une vue à 360 degrés de toutes les interactions et activités liées à un client spécifique.

Ce chapitre vous a donné les bases pour gérer vos clients dans ClientDocManager. Explorez les différentes options et n'hésitez pas à consulter les autres chapitres pour des fonctionnalités plus spécifiques comme la création de documents pour ces clients.
