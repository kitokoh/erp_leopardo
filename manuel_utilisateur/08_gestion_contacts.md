# Chapitre 8 : Gestion des Contacts

En plus de la gestion de vos clients (qui sont des entreprises ou des entités), ClientDocManager vous permet de gérer un carnet d'adresses détaillé pour les **personnes** avec qui vous interagissez. Ce module "Contacts" peut inclure des contacts liés à vos clients, mais aussi des prospects, des partenaires, des fournisseurs, ou tout autre contact professionnel. Une fonctionnalité notable est la synchronisation avec Google Contacts.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 8.1. Accéder au Module Contacts

1.  Repérez le **Volet de Navigation Principal**.
2.  Cliquez sur l'icône ou le libellé **Contacts** ou **Carnet d'adresses**.
3.  La **Zone d'Affichage Principale** affichera la liste de vos contacts.

## 8.2. L'Interface du Module Contacts

L'interface de gestion des contacts est similaire à celle des clients ou des produits :

*   **Liste des Contacts**:
    *   Un tableau affichant vos contacts avec des colonnes comme : Nom, Prénom, Société Associée, Fonction, E-mail Principal, Téléphone Principal.
    *   **Barre de recherche**: Pour rechercher un contact par nom, société, e-mail, etc.
    *   **Options de tri et de filtrage**.
*   **Barre d'Outils Spécifique**:
    *   **Nouveau Contact**: Pour créer une nouvelle fiche contact.
    *   **Modifier Contact**: Pour éditer le contact sélectionné.
    *   **Supprimer Contact**: Pour enlever le contact sélectionné.
    *   **Synchroniser avec Google Contacts** (si configuré).

## 8.3. Créer un Nouveau Contact

1.  Dans le module Contacts, cliquez sur le bouton **Nouveau Contact**.
2.  La fenêtre (dialogue) **Ajouter un Nouveau Contact** (`ContactDialog`) s'ouvrira.
3.  Remplissez les informations :
    *   **Informations Personnelles**: Civilité (M., Mme, etc.), Nom, Prénom, Fonction/Titre.
    *   **Société Associée**: Vous pouvez lier ce contact à une société cliente existante (sélection depuis la liste de vos clients - voir [Chapitre 3](./03_gestion_clients.md)) ou saisir le nom d'une nouvelle société (qui pourrait alors être créée comme prospect ou client).
    *   **Coordonnées Multiples**:
        *   Plusieurs adresses e-mail (professionnel, personnel) avec indication du type.
        *   Plusieurs numéros de téléphone (mobile, bureau, fax) avec indication du type.
    *   **Adresse(s)**: Adresse postale du contact.
    *   **Notes**: Commentaires spécifiques sur ce contact.
    *   **Tags/Catégories**: Pour classer ou segmenter vos contacts.
4.  Cliquez sur **OK** ou **Enregistrer**.

## 8.4. Rechercher un Contact

Utilisez le champ **Recherche** au-dessus de la liste des contacts pour trouver rapidement une personne.

## 8.5. Modifier un Contact

1.  **Sélectionnez le contact** dans la liste.
2.  Cliquez sur **Modifier Contact**.
3.  Le dialogue s'ouvrira avec les informations actuelles, que vous pourrez modifier.
4.  Cliquez sur **OK** ou **Enregistrer**.

## 8.6. Supprimer un Contact

1.  **Sélectionnez le contact**.
2.  Cliquez sur **Supprimer Contact**.
3.  Confirmez votre choix.

## 8.7. Synchronisation avec Google Contacts

ClientDocManager peut vous permettre de synchroniser votre carnet d'adresses local avec vos contacts Google.

### 8.7.1. Configuration de la Synchronisation Google

1.  Allez dans les **Paramètres** de l'application (généralement via **Fichier > Paramètres** ou une icône d'engrenage).
2.  Cherchez une section "Synchronisation", "Comptes en ligne", ou "Google Contacts" (`GoogleSettingsDialog`).
3.  **Autorisation Initiale**:
    *   Vous devrez autoriser ClientDocManager à accéder à vos contacts Google. Cliquez sur un bouton comme **Connecter à Google** ou **Autoriser**.
    *   Cela ouvrira généralement une page web dans votre navigateur où vous devrez vous connecter à votre compte Google et accorder les permissions demandées par l'application.
    *   Suivez les instructions à l'écran.
4.  **Paramètres de Synchronisation**: Une fois autorisé, vous pourrez peut-être configurer :
    *   Le **sens de la synchronisation**:
        *   *Bidirectionnelle* : Les modifications faites dans ClientDocManager sont envoyées à Google, et vice-versa.
        *   *ClientDocManager vers Google* : Seules les modifications locales sont envoyées à Google.
        *   *Google vers ClientDocManager* : Seules les modifications Google sont récupérées localement.
    *   La **fréquence de synchronisation**: Automatique (toutes les X minutes/heures) ou manuelle.
    *   Des options de **résolution de conflits** (par exemple, "toujours demander", "le plus récent l'emporte").
5.  Enregistrez vos paramètres.

### 8.7.2. Lancer une Synchronisation Manuelle

*   Dans le module Contacts ou dans les paramètres de synchronisation Google, il peut y avoir un bouton **Synchroniser Maintenant** pour forcer une synchronisation immédiate.

### 8.7.3. Comment Fonctionne la Synchronisation ?

*   Le service de synchronisation (`SyncService`) compare les contacts de votre base de données ClientDocManager avec ceux de votre compte Google Contacts.
*   Il identifie les nouveaux contacts, les contacts modifiés, et les contacts supprimés de chaque côté.
*   En fonction de vos paramètres de synchronisation, il effectue les ajouts, modifications ou suppressions nécessaires pour que les deux carnets d'adresses soient alignés.
*   **Attention aux conflits**: Si un même contact a été modifié différemment des deux côtés depuis la dernière synchronisation, un conflit peut survenir. La manière dont il est résolu dépend de vos paramètres ou peut nécessiter une intervention manuelle.

## 8.8. Utilisation des Contacts

Une fois vos contacts enregistrés et organisés (et éventuellement synchronisés) :
*   Vous pouvez facilement retrouver leurs coordonnées.
*   Lorsque vous créez un e-mail depuis l'application, vous pouvez sélectionner des destinataires depuis ce carnet d'adresses.
*   Ils peuvent être liés à des clients, des projets, ou d'autres entités pour un meilleur suivi relationnel.

Une gestion rigoureuse de vos contacts est un atout pour votre communication et votre organisation commerciale.
