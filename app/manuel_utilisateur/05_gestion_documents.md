# Chapitre 5 : Création et Gestion de Documents (désormais partie intégrante de la Gestion Client)

ClientDocManager est conçu pour simplifier la création et la gestion de vos documents commerciaux et administratifs. Ce chapitre vous montrera comment générer de nouveaux documents à partir de modèles, les organiser et les retrouver.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 5.1. Types de Documents Gérés

L'application vous permet de générer divers types de documents, tels que (liste non exhaustive) :

*   Factures Proforma
*   Factures Finales (voir aussi [Chapitre 6 : Facturation et Suivi des Paiements](./06_facturation_paiements.md))
*   Devis ou Offres Commerciales
*   Contrats de Vente
*   Spécifications Techniques
*   Bons de Commande
*   Bons de Livraison / Packing Lists
*   Documents de Garantie
*   Pages de Contact personnalisées
*   Pages de Garde pour des compilations PDF

La liste exacte des documents que vous pouvez générer dépend des modèles configurés dans votre application (voir [Module Paramètres et Configuration](../cahier/desktop/module_parametres_configuration.md) pour les aspects techniques, ou demandez à votre administrateur).

## 5.2. Accéder à la Gestion des Documents (via la Gestion Client)

Les fonctionnalités de gestion documentaire sont maintenant principalement accessibles via la **Gestion Client**:

*   **Depuis la Fiche Client**: En consultant un client ([Chapitre 3](./03_gestion_clients.md)), vous trouverez un onglet ou une section "Documents" listant tous les documents associés à ce client. C'est ici que vous pourrez créer un nouveau document pour lui.
*   Un module "Documents" global (s'il existait) est désormais intégré ou remplacé par la vue centrée sur le client.
*   **Depuis la Fenêtre Principale**: Le menu **Fichier > Nouveau > Document** (ou un type de document spécifique) peut être disponible.

## 5.3. Créer un Nouveau Document (Exemple : une Facture Proforma)

Le processus de création d'un nouveau document est généralement similaire, quel que soit son type. Prenons l'exemple de la création d'une facture proforma :

1.  **Initier la Création**:
    *   Soit depuis la fiche d'un client, cliquez sur **Créer Document > Facture Proforma**.
    *   Soit depuis un module "Documents" ou "Factures Proforma", cliquez sur **Nouvelle Facture Proforma**.
2.  **Dialogue de Création de Document (`CreateDocumentDialog` ou similaire)**:
    *   Une fenêtre de dialogue s'ouvre.
    *   **Sélection du Client**: Si vous n'avez pas initié la création depuis une fiche client, vous devrez sélectionner le client concerné. Une recherche ou une liste déroulante des clients existants sera proposée.
    *   **Sélection du Modèle**: L'application peut proposer un modèle par défaut pour ce type de document et cette langue, ou vous permettre de choisir parmi les modèles disponibles.
    *   **Informations du Document**:
        *   `Date du document`: Pré-remplie avec la date du jour, modifiable.
        *   `Numéro de document`: Peut être généré automatiquement ou nécessiter une saisie (selon la configuration).
        *   `Objet` ou `Référence`: Un champ pour un titre ou une référence interne.
        *   `Validité` (pour les devis/proformas).
        *   `Conditions de paiement`, `Mode de règlement`.
    *   **Ajout de Lignes de Produits/Services**:
        *   Cliquez sur un bouton **Ajouter Ligne** ou **Ajouter Produit**.
        *   Une nouvelle ligne apparaît. Vous pouvez y rechercher et sélectionner un produit/service de votre catalogue ([Chapitre 4](./04_gestion_produits.md)).
        *   La description, le prix unitaire et le taux de TVA peuvent être automatiquement remplis à partir de la fiche produit.
        *   Saisissez la `Quantité`.
        *   Le `Prix total` de la ligne et les `Taxes` sont calculés.
        *   Vous pouvez souvent modifier la description ou le prix unitaire pour cette ligne spécifique sans altérer la fiche produit originale.
        *   Ajoutez autant de lignes que nécessaire.
    *   **Totaux**: Les totaux (HT, TVA, TTC) sont calculés automatiquement en bas du document.
    *   **Notes / Mentions Spéciales**: Un champ pour ajouter des commentaires ou des clauses particulières.
3.  **Validation et Génération**:
    *   Une fois toutes les informations saisies, cliquez sur **Générer**, **OK**, ou **Enregistrer**.
    *   L'application utilise les informations fournies et le modèle sélectionné pour :
        1.  Préparer le contexte de données (informations client, produits, totaux, etc.).
        2.  Remplir le modèle (HTML ou DOCX) avec ces données.
        3.  Si le format final est PDF (pour les documents HTML), convertir le document en PDF.
4.  **Sauvegarde et Affichage**:
    *   Le document généré (ex: PDF, DOCX) est sauvegardé (l'emplacement peut être configuré ou être un dossier spécifique au client).
    *   Les informations (métadonnées) sur ce document (type, numéro, client, date, chemin du fichier) sont enregistrées dans la base de données.
    *   Le document peut s'ouvrir automatiquement pour prévisualisation.
    *   Une notification de succès s'affiche.

## 5.4. Retrouver et Gérer les Documents Existants

*   **Listes de Documents**:
    *   Dans le module "Documents" ou dans les onglets "Documents" des fiches clients/projets, vous verrez la liste des documents existants.
    *   Utilisez les fonctions de **recherche** et de **filtrage** (par type, date, client, statut) pour retrouver un document spécifique.
*   **Actions sur les Documents**:
    *   **Ouvrir/Prévisualiser**: Sélectionnez un document et cliquez sur **Ouvrir** ou double-cliquez dessus pour l'afficher dans son application par défaut (ex: Adobe Reader pour les PDF, Microsoft Word pour les DOCX).
    *   **Modifier**:
        *   Pour certains documents (notamment ceux basés sur des modèles Excel ou Word avant leur "finalisation" en PDF), une option **Modifier** peut rouvrir le dialogue de création avec les données pré-remplies ou ouvrir le fichier dans un éditeur intégré/externe.
        *   Les PDF finalisés ne sont généralement pas modifiables directement de cette manière (sauf via des outils d'édition PDF spécialisés).
    *   **Supprimer**: Supprime le document de la liste et potentiellement le fichier du disque (avec confirmation).
    *   **Dupliquer**: Crée une copie d'un document existant, que vous pouvez ensuite modifier. Utile pour créer rapidement un nouveau document basé sur un précédent.
    *   **Envoyer par E-mail**: Ouvre le dialogue d'envoi d'e-mail ([Chapitre sur la Gestion des E-mails UI](./module_gestion_emails_ui.md)) avec le document sélectionné en pièce jointe.
    *   **Compiler en PDF (pour plusieurs PDF)**: Si vous sélectionnez plusieurs fichiers PDF, une option pour les assembler en un seul PDF (avec potentiellement une page de garde) peut être disponible.

## 5.5. Organisation des Fichiers

*   ClientDocManager peut organiser les fichiers de documents générés dans une structure de dossiers sur votre ordinateur ou un lecteur réseau.
*   Souvent, les documents sont classés par client, puis par type de document ou par date.
*   L'emplacement de stockage principal est généralement configurable dans les [Paramètres](./98_parametres_utilisateur.md) de l'application.

La maîtrise de la création et de la gestion des documents est essentielle pour tirer pleinement parti de ClientDocManager. N'hésitez pas à explorer les différentes options de création et les actions disponibles sur les documents existants.
