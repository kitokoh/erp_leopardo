# Chapitre 6 : Facturation et Suivi des Paiements

La facturation et le suivi des paiements sont des aspects critiques de la gestion de toute entreprise. ClientDocManager vous aide à créer des factures professionnelles, à les envoyer à vos clients, et à enregistrer les paiements reçus pour maintenir une comptabilité claire.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 6.1. Accéder au Module Facturation

Les fonctionnalités de facturation peuvent être accessibles de plusieurs manières :

*   **Module "Factures" ou "Facturation" dédié**: Dans le **Volet de Navigation Principal**, cherchez une entrée spécifique pour les factures.
*   **Depuis une Facture Proforma Acceptée**: Vous pourriez avoir une option pour convertir une facture proforma existante et acceptée en une facture finale.
*   **Depuis la Fiche Client**: Un bouton "Créer Facture" peut être disponible sur la fiche d'un client.

## 6.2. L'Interface du Module Facturation

L'interface de gestion des factures (`InvoiceManagementWidget`) est similaire à celle d'autres listes :

*   **Liste des Factures**:
    *   Affiche les factures avec des colonnes comme : Numéro de Facture, Client, Date d'Émission, Date d'Échéance, Montant Total, Statut (Brouillon, Envoyée, Payée, Partiellement Payée, En Retard, Annulée).
    *   Options de recherche, tri, et filtrage (par exemple, afficher toutes les factures "En Retard").
*   **Barre d'Outils Spécifique**:
    *   **Nouvelle Facture**: Pour créer une facture de zéro.
    *   **Modifier Facture**: Uniquement si la facture est encore à l'état de "Brouillon". Une fois finalisée ou envoyée, les modifications sont généralement interdites (il faut alors passer par un avoir).
    *   **Visualiser/Imprimer Facture**: Pour ouvrir le PDF de la facture.
    *   **Envoyer par E-mail**: Pour envoyer la facture au client.
    *   **Enregistrer Paiement**: Pour marquer un paiement reçu pour la facture sélectionnée.
    *   **Annuler Facture**: Pour annuler une facture (avec des implications comptables).

## 6.3. Créer une Facture Finale

Il y a généralement deux manières principales de créer une facture finale :

### 6.3.1. Créer une Facture à partir d'une Proforma

C'est souvent la méthode la plus simple si vous avez déjà émis une facture proforma qui a été acceptée par le client.

1.  Retrouvez la facture proforma concernée (voir [Chapitre 5](./05_gestion_documents.md)).
2.  Sélectionnez la proforma. Il devrait y avoir une action ou un bouton comme **Convertir en Facture** ou **Générer Facture Finale**.
3.  Un dialogue de confirmation ou de finalisation (`FinalInvoiceDataDialog`) peut s'ouvrir.
    *   Il peut vous demander de confirmer la date de la facture finale.
    *   Un nouveau numéro de facture (distinct de la proforma) sera assigné automatiquement selon la séquence configurée.
    *   Les lignes de produits/services et les montants seront repris de la proforma. Vous pourriez avoir une dernière chance de faire des ajustements mineurs si la configuration le permet.
4.  Validez. La facture finale est créée et enregistrée. La facture proforma d'origine peut être marquée comme "Convertie".

### 6.3.2. Créer une Facture Finale de Zéro (`ManualInvoiceDialog`)

1.  Cliquez sur **Nouvelle Facture** dans le module de facturation.
2.  Le dialogue de création de facture s'ouvre. Il est très similaire au dialogue de création de proforma :
    *   Sélectionnez le **Client**.
    *   Entrez une **Date de Facture** et une **Date d'Échéance**.
    *   Ajoutez les **lignes de produits/services** avec quantités, prix unitaires, et taux de TVA.
    *   Vérifiez les **conditions de paiement**.
    *   Ajoutez des **notes** si nécessaire.
3.  Le **Numéro de Facture** sera généralement assigné automatiquement par le système lors de la sauvegarde pour garantir une séquence unique et continue.
4.  Cliquez sur **Enregistrer** ou **Générer**.
5.  La facture est enregistrée (souvent d'abord comme "Brouillon"). Vous pouvez ensuite la **Finaliser** ou la **Valider**, ce qui la rend non modifiable et prête à être envoyée.

## 6.4. Envoyer une Facture au Client

1.  Sélectionnez la facture finalisée dans la liste.
2.  Cliquez sur le bouton **Envoyer par E-mail**.
3.  Le dialogue d'envoi d'e-mail s'ouvrira ([Chapitre sur la Gestion des E-mails UI](./module_gestion_emails_ui.md)), avec la facture PDF automatiquement attachée et potentiellement un modèle d'e-mail pré-chargé.
4.  Vérifiez/complétez les informations de l'e-mail et envoyez.
5.  Le statut de la facture peut passer à "Envoyée".

## 6.5. Enregistrer un Paiement (`RecordPaymentDialog`)

Lorsqu'un client effectue un paiement pour une facture :

1.  Retrouvez et sélectionnez la facture concernée dans la liste.
2.  Cliquez sur le bouton **Enregistrer Paiement**.
3.  Le dialogue **Enregistrer un Paiement** s'ouvre :
    *   La facture et son montant dû sont généralement affichés.
    *   `Date du paiement`: Saisissez la date à laquelle vous avez reçu le paiement.
    *   `Montant payé`: Saisissez le montant exact reçu. Ce peut être un paiement partiel ou total.
    *   `Mode de paiement`: Sélectionnez comment le paiement a été effectué (Virement, Chèque, Espèces, Carte, etc.).
    *   `Référence du paiement`: (Ex: numéro de chèque, référence de virement).
    *   `Notes`: Commentaires optionnels.
4.  Cliquez sur **OK** ou **Enregistrer**.
5.  Le paiement est enregistré en base de données.
6.  Le statut de la facture est mis à jour :
    *   Si le montant payé couvre le total de la facture, le statut passe à **Payée**.
    *   Si le montant payé est inférieur au total, le statut passe à **Partiellement Payée**, et le solde restant dû est mis à jour.
7.  Vous pouvez enregistrer plusieurs paiements partiels pour une même facture jusqu'à ce qu'elle soit entièrement réglée.

## 6.6. Suivi des Factures Impayées et des Retards

*   Utilisez les filtres de la liste des factures pour afficher les factures **Impayées**, **Partiellement Payées**, ou **En Retard** (celles dont la date d'échéance est dépassée et qui ne sont pas entièrement payées).
*   Certaines versions peuvent inclure des indicateurs visuels (couleurs) pour les factures en retard.
*   Des fonctionnalités de **relance client** (manuelle ou semi-automatisée par e-mail) peuvent être disponibles pour les factures impayées.

## 6.7. Gestion des Avoirs (Notes de Crédit)

Si un client retourne des marchandises, si une erreur a été commise sur une facture déjà finalisée, ou pour toute autre raison nécessitant un remboursement ou une réduction, vous devrez créer un **avoir** (ou note de crédit).

*   Le processus de création d'un avoir est similaire à celui d'une facture, mais les montants sont généralement négatifs ou indiquent un crédit.
*   L'avoir peut être lié à une facture spécifique ou être indépendant.
*   Les avoirs impactent le solde dû par le client.

*(La gestion des avoirs est une fonctionnalité comptable importante. Vérifiez si elle est explicitement supportée et comment elle est implémentée dans votre version de ClientDocManager).*

## 6.8. Aspects Comptables (Dépenses)

Comme mentionné dans la documentation technique ([Module Facturation et Paiements](../cahier/desktop/module_facturation_paiements.md)), l'application peut aussi inclure des fonctionnalités pour enregistrer :
*   Les **dépenses de l'entreprise**.
*   Les **factures fournisseurs**.

Si ces fonctionnalités ont une interface utilisateur dédiée, elles seraient accessibles via un menu ou une section spécifique, permettant de saisir les détails des dépenses (date, montant, fournisseur, catégorie, justificatif).

Une bonne gestion de la facturation et des paiements est vitale pour la santé financière de votre entreprise. Prenez le temps de bien comprendre ces fonctionnalités dans ClientDocManager.
