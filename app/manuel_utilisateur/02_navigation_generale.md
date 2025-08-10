# Chapitre 2 : Prise en Main - Navigation Générale

Une fois connecté à ClientDocManager, vous arrivez sur la fenêtre principale, souvent appelée `DocumentManager`. Ce chapitre vous présente les éléments clés de cette interface et comment naviguer entre les différentes fonctionnalités.

*(Des captures d'écran seront ajoutées ultérieurement pour illustrer ces descriptions)*

## 2.1. Vue d'Ensemble de la Fenêtre Principale

La fenêtre principale de ClientDocManager est généralement composée des zones suivantes :

*   **Barre de Menu (en haut)**:
    *   Contient les menus déroulants classiques comme **Fichier**, **Édition**, **Vue**, **Outils**, **Fenêtre**, **Aide**.
    *   **Fichier**: Peut inclure des options comme *Nouveau (Client, Document, etc.)*, *Ouvrir*, *Paramètres*, *Quitter*.
    *   **Outils**: Peut donner accès à des modules spécifiques comme la *Gestion des Utilisateurs*, la *Configuration des Modèles*, etc. (souvent réservé aux administrateurs).
    *   **Aide**: Accès à la documentation, "À propos de ClientDocManager".

*   **Barre d'Outils (sous la barre de menu)**:
    *   Contient des icônes pour un accès rapide aux actions les plus fréquentes (ex: Nouveau Client, Nouveau Document, Rechercher, Enregistrer).
    *   Le contenu de la barre d'outils peut parfois changer en fonction du module actif.

*   **Volet de Navigation Principal / Panneau Latéral (souvent à gauche)**:
    *   C'est votre principal moyen pour accéder aux différents modules de l'application.
    *   Il peut se présenter sous forme d'une liste d'icônes, d'une arborescence, ou d'onglets verticaux.
    *   Exemples de sections accessibles :
        *   Tableau de Bord / Accueil
        *   Clients
        *   Produits
        *   Documents (ou types de documents spécifiques comme Devis, Factures)
        *   Projets
        *   Contacts
        *   Recrutement
        *   Calendrier
        *   Statistiques/Rapports
        *   Paramètres (souvent avec une icône d'engrenage)

*   **Zone d'Affichage Principale (au centre)**:
    *   C'est la plus grande partie de la fenêtre. Son contenu change dynamiquement en fonction du module que vous avez sélectionné dans le volet de navigation.
    *   Si vous sélectionnez "Clients", cette zone affichera la liste de vos clients.
    *   Si vous travaillez sur un document, l'éditeur ou la prévisualisation du document s'affichera ici.
    *   Elle peut contenir des tableaux de données, des formulaires de saisie, des graphiques, des éditeurs de texte, etc.

*   **Barre d'État (en bas)**:
    *   Peut afficher des informations contextuelles :
        *   Nom de l'utilisateur connecté.
        *   Version de l'application.
        *   Messages d'état temporaires (ex: "Sauvegarde en cours...").
        *   Nombre d'éléments dans une liste affichée.

## 2.2. Naviguer entre les Modules

1.  **Utiliser le Volet de Navigation Principal**:
    *   Cliquez sur l'icône ou le nom du module que vous souhaitez ouvrir (ex: **Clients**, **Produits**, **Factures**).
    *   La Zone d'Affichage Principale se mettra à jour pour afficher l'interface correspondante à ce module.

2.  **Utiliser la Barre de Menu**:
    *   Certains modules ou actions spécifiques peuvent aussi être accessibles via les options de la barre de menu (ex: **Fichier > Nouveau > Client**).

## 2.3. Actions Courantes dans les Modules

Bien que chaque module ait ses spécificités, vous retrouverez souvent des actions similaires :

*   **Créer un nouvel élément**: Recherchez un bouton **+ Nouveau**, **Ajouter**, ou une option de menu comme **Fichier > Nouveau > [Type d'élément]**.
*   **Modifier un élément existant**:
    *   Sélectionnez l'élément dans une liste ou un tableau.
    *   Cliquez sur un bouton **Modifier** (souvent une icône de crayon) ou double-cliquez sur l'élément.
    *   Un clic droit sur l'élément peut aussi faire apparaître un menu contextuel avec l'option **Modifier**.
*   **Supprimer un élément existant**:
    *   Sélectionnez l'élément.
    *   Cliquez sur un bouton **Supprimer** (souvent une icône de corbeille) ou utilisez le menu contextuel.
    *   Une confirmation vous sera généralement demandée avant la suppression définitive.
*   **Rechercher**: La plupart des listes (clients, produits, documents) disposeront d'un champ de recherche pour filtrer rapidement les résultats.
*   **Filtrer et Trier les Listes**: Les colonnes des tableaux peuvent souvent être cliquées pour trier les données. Des options de filtrage plus avancées peuvent être disponibles via des listes déroulantes ou des panneaux de filtres.

## 2.4. Utilisation des Dialogues

De nombreuses actions (comme la création ou la modification d'un client, d'un produit, d'un document) ouvriront une nouvelle fenêtre appelée **dialogue** (ou fenêtre modale).

*   Ces dialogues se superposent à la fenêtre principale et requièrent votre attention.
*   Vous devez généralement remplir les champs demandés et ensuite cliquer sur un bouton comme **OK**, **Enregistrer**, **Valider** pour appliquer les changements, ou **Annuler** pour fermer le dialogue sans sauvegarder.

## 2.5. Se Déconnecter et Quitter

*   **Se Déconnecter**: Si vous souhaitez changer d'utilisateur sans fermer l'application, cherchez une option comme **Fichier > Déconnexion** ou un bouton de déconnexion (souvent une icône de porte de sortie). Cela vous ramènera généralement au dialogue de connexion.
*   **Quitter l'Application**: Pour fermer complètement ClientDocManager, utilisez l'option **Fichier > Quitter** ou le bouton de fermeture standard de la fenêtre de votre système d'exploitation (la croix en haut à droite sur Windows/Linux, le rond rouge sur macOS).

Prenez un moment pour vous familiariser avec ces éléments. Une bonne compréhension de la navigation générale vous aidera à utiliser toutes les fonctionnalités de ClientDocManager plus efficacement. Les chapitres suivants de ce manuel décriront en détail l'utilisation de chaque module spécifique.
