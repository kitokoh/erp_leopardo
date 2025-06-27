# Interfaces Utilisateur (UI) et Flux de Navigation

Ce document donne un aperçu des interfaces utilisateur (UI) de l'application Client Document Manager, à la fois pour la version de bureau (PyQt5) et l'application mobile (Kivy). Il décrit également certains flux de navigation clés.

## 1. Application Desktop (PyQt5)

L'interface utilisateur de l'application de bureau est conçue pour être riche en fonctionnalités, permettant un accès complet à toutes les capacités de gestion.

### 1.1. Principes Généraux de l'UI Desktop

*   **Fenêtre Principale (`main_window.py` - `DocumentManager`)**:
    *   Sert de conteneur principal pour la plupart des fonctionnalités.
    *   Comprend généralement une barre de menus, une barre d'outils, un panneau de navigation latéral et une zone d'affichage centrale.
*   **Navigation**:
    *   Panneau latéral avec des icônes ou des entrées de texte pour accéder aux différents modules (Clients, Produits, Projets, Factures, Paramètres, etc.).
    *   Barre de menus pour des actions globales (Fichier, Édition, Vue, Outils, Aide).
*   **Affichage des Données**:
    *   Utilisation intensive de tableaux (`QTableView`) pour afficher des listes de données (clients, produits, factures). Ces tableaux permettent le tri, le filtrage et la recherche.
    *   Formulaires (`QFormLayout`, `QGridLayout`) pour l'entrée et l'édition de données détaillées.
*   **Dialogues Modaux et Non-Modaux**:
    *   De nombreuses actions (ajout, édition, confirmation) ouvrent des fenêtres de dialogue (`QDialog`) spécifiques.
*   **Gestion des Thèmes/Styles**: L'application utilise un fichier `style.qss` pour une apparence personnalisée.
*   **Internationalisation**: L'interface est traduite dans plusieurs langues (fichiers `.ts` et `.qm` dans `translations/`).

### 1.2. Écrans et Composants Clés de l'UI Desktop

*   **Tableau de Bord (Accueil - `home_page_widget.py`)**:
    *   Affiche un résumé des informations importantes, des statistiques clés, des raccourcis vers les actions fréquentes.
*   **Gestion des Clients (`client_widget.py`, `dialogs/add_new_client_dialog.py`, `dialogs/edit_client_dialog.py`)**:
    *   Liste des clients avec recherche et filtres.
    *   Vue détaillée d'un client affichant ses informations, projets, documents, contacts.
    *   Dialogues pour ajouter ou modifier un client.
*   **Gestion des Produits (`product_management/page.py`, `product_management/list_dialog.py`, `product_management/edit_dialog.py`)**:
    *   Liste des produits avec recherche et filtres.
    *   Dialogues pour ajouter ou modifier des produits.
*   **Gestion des Documents (Intégrée dans les modules clients, projets, etc.)**:
    *   Listes de documents associés à un client ou un projet.
    *   `dialogs/create_document_dialog.py`: Dialogue pour sélectionner un type de document à générer, choisir un modèle, une langue.
    *   `document_generator/` et `pagedegrde.py`: Bien que principalement logiques, ils ont des implications sur l'UI pour la prévisualisation ou la sélection d'options de page de garde.
    *   `excel_editor.py`: Interface pour l'édition basique de fichiers Excel.
*   **Gestion des Factures et Proformas (`invoicing/invoice_management_widget.py`, `dialogs/proforma_invoice_utils.py`)**:
    *   Listes de factures et proformas.
    *   Dialogues pour créer/éditer des factures, enregistrer des paiements.
*   **Gestion de Projets (`project_management/dashboard.py`, dialogues associés)**:
    *   Tableau de bord des projets.
    *   Listes de projets, tâches, jalons.
    *   Dialogues pour la gestion des ordres de production, etc.
*   **Recrutement (`recruitment/recruitment_dashboard.py`, widgets et dialogues associés)**:
    *   Tableau de bord du recrutement.
    *   Gestion des offres d'emploi, des candidats, des entretiens.
*   **Paramètres (`settings_page.py`, `security_settings_page.py`)**:
    *   Interface pour configurer l'application (SMTP, chemins de dossiers, modèles par défaut, utilisateurs, rôles, etc.).
*   **Authentification (`dialogs/login_dialog.py`)**:
    *   Dialogue de connexion affiché au démarrage.

### 1.3. Flux de Navigation Typiques (Desktop)

*   **Connexion -> Tableau de Bord**:
    1.  Lancement de l'application.
    2.  `LoginDialog` s'affiche.
    3.  Utilisateur entre ses identifiants.
    4.  Si succès, `DocumentManager` (fenêtre principale) s'affiche, souvent sur le `HomePageWidget`.
*   **Consulter et Éditer un Client**:
    1.  Depuis le panneau de navigation, sélectionne "Clients".
    2.  La liste des clients s'affiche dans la zone centrale.
    3.  Utilisateur recherche/sélectionne un client.
    4.  Double-clic ou bouton "Éditer" ouvre `EditClientDialog` avec les informations du client.
    5.  Modification des informations, puis "Sauvegarder".
*   **Générer une Facture Proforma pour un Client**:
    1.  Naviguer vers la fiche du client concerné.
    2.  Bouton "Générer Document" ou action similaire.
    3.  `CreateDocumentDialog` s'ouvre.
    4.  Sélectionner "Facture Proforma", langue, modèle (si plusieurs).
    5.  Un dialogue spécifique à la proforma s'ouvre pour ajouter des produits/lignes.
    6.  Valider pour générer le document. Prévisualisation ou option de sauvegarde/envoi.

## 2. Application Mobile (Kivy)

L'interface utilisateur de l'application mobile est conçue pour être simple, intuitive et adaptée aux interactions tactiles.

### 2.1. Principes Généraux de l'UI Mobile

*   **Navigation par Écrans (`ScreenManager` de Kivy)**:
    *   L'application est composée de plusieurs écrans entre lesquels l'utilisateur navigue.
    *   Menu hamburger, barre d'onglets en bas, ou boutons de navigation pour passer d'un écran à l'autre.
*   **Conception Adaptée au Mobile**:
    *   Utilisation de widgets Kivy adaptés (boutons, listes déroulantes (`Spinner`), champs de texte, listes (`RecycleView`)).
    *   Disposition réactive pour s'adapter à différentes tailles d'écran (bien que Kivy gère cela en partie).
*   **Interaction Tactile**: Optimisée pour les gestes tactiles.
*   **Retour Visuel**: Indicateurs de chargement pour les opérations longues (appels API).

### 2.2. Écrans et Composants Clés de l'UI Mobile

(Basé sur l'analyse de `cahier/mobile/` et `mobile/mobile.kv` si disponible)

*   **Écran de Connexion (si authentification mobile dédiée)**:
    *   Champs pour nom d'utilisateur/mot de passe pour l'API.
*   **Écran d'Accueil/Principal**:
    *   Menu principal ou tableau de bord simple avec accès aux fonctionnalités clés.
*   **Écran de Génération de Documents (`DocumentGenerationScreen` ou similaire)**:
    *   Interface principale pour la génération de documents (ex: proformas).
    *   Champs de sélection (Spinners Kivy) pour :
        *   Langue
        *   Pays/Client (si applicable)
        *   Type de document / Modèle
        *   Produits (sélection multiple ou ajout de lignes)
    *   Bouton pour initier la génération.
    *   Zone pour afficher le statut ou le résultat (ex: lien vers le PDF généré).
*   **Écran de Liste de Produits (Consultation)**:
    *   Affichage simple des produits disponibles (nom, référence, prix).
    *   Peut-être une fonction de recherche basique.
*   **Écran de Liste de Clients (Consultation)**:
    *   Affichage simple des clients.
*   **Interface NLU (si active)**:
    *   Champ de texte pour entrer des commandes en langage naturel.
    *   Affichage des résultats ou actions déclenchées par le NLU.
*   **Interaction avec Plyer**:
    *   L'UI déclenche des appels à Plyer pour des actions comme :
        *   Partager un fichier (`plyer.sharing.share_file()`).
        *   Envoyer un e-mail (`plyer.email.send()`).
        *   Sélectionner un fichier (`plyer.filechooser.open_file()`) - moins probable si les modèles sont du serveur.

### 2.3. Flux de Navigation Typiques (Mobile)

*   **Générer une Proforma PDF**:
    1.  Ouvrir l'application.
    2.  (Si authentification) Se connecter.
    3.  Naviguer vers l'écran "Générer Document".
    4.  Sélectionner la langue, le client (si liste déroulante), les produits et leurs quantités.
    5.  Choisir le modèle "Facture Proforma".
    6.  Appuyer sur "Générer PDF".
    7.  Un indicateur de progression s'affiche pendant que l'application :
        a.  Génère le HTML localement avec Jinja2.
        b.  Envoie le HTML à l'API backend pour conversion.
        c.  Télécharge le PDF résultant.
    8.  Une fois le PDF reçu, l'UI affiche un message de succès et propose des options : "Ouvrir", "Partager", "Envoyer par e-mail".
    9.  L'utilisateur choisit une action, qui utilise Plyer pour interagir avec le système d'exploitation mobile.

*   **Consulter la Liste des Produits**:
    1.  Naviguer vers l'écran "Produits" ou "Catalogue".
    2.  L'application effectue un appel API pour récupérer la liste des produits.
    3.  La liste des produits s'affiche dans une `RecycleView` ou un widget similaire.
    4.  L'utilisateur peut faire défiler la liste.

## 3. Cohérence et Expérience Utilisateur (UX)

*   **Desktop**: L'UX vise l'exhaustivité et la puissance, permettant des opérations complexes et la gestion de grands volumes de données. La courbe d'apprentissage peut être plus élevée.
*   **Mobile**: L'UX privilégie la simplicité et la rapidité pour des tâches ciblées en situation de mobilité. Les fonctionnalités sont un sous-ensemble de celles de l'application de bureau.
*   Une certaine cohérence visuelle (logos, couleurs primaires si possible) et terminologique entre les deux plateformes peut améliorer l'expérience globale, bien que les paradigmes d'interface soient différents.

Ce document fournit un aperçu général. Des maquettes d'interface utilisateur (wireframes ou mockups) seraient nécessaires pour une conception UI/UX détaillée, mais cela dépasse le cadre de la documentation de l'architecture existante. Les diagrammes de flux d'utilisateur pourraient également être utiles pour visualiser ces navigations.
