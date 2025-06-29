# Module : Rapports et Statistiques (Desktop)

## 1. Objectif Principal

Le module de Rapports et Statistiques de ClientDocManager a pour but de fournir aux utilisateurs des outils pour visualiser, analyser et exporter des données consolidées issues des différentes opérations gérées par l'application. L'objectif est d'offrir une meilleure compréhension de la performance de l'entreprise, des tendances, et d'aider à la prise de décision éclairée.

## 2. Composants Clés et Fonctionnalités

*   **Interface d'Affichage des Rapports et Statistiques**:
    *   **`statistics_page_widget.py`**: Widget principal ou page dédiée à l'affichage des rapports et des statistiques (principalement pour les vues agrégées globales).
    *   **`statistics_panel.py`**: Panneau ou section spécifique (souvent pliable) au sein de la `statistics_page_widget` ou d'autres tableaux de bord pour afficher des graphiques ou des chiffres clés.
    *   **`statistics_module.py`**: Contient la logique de présentation principale, y compris le `StatisticsDashboard` (qui intègre une carte interactive et des statistiques globales) et le nouvel `AdvancedReportingTool`. Ce module gère la récupération des données formatées pour l'affichage et la définition des types de graphiques.

*   **Génération des Données de Rapports (Backend/Logique)**:
    *   **`api/reports.py`**: (Rôle potentiellement réduit pour les rapports personnalisés directs depuis l'UI) Ce module API peut toujours être utilisé pour des rapports complexes, prédéfinis ou ceux nécessitant une logique backend importante non directement exposée via les CRUDs.
    *   **`db/cruds/`**: Les modules CRUD spécifiques ont été étendus pour supporter le reporting avancé :
        *   **`db/cruds/proforma_invoices_crud.py`**: Contient `get_sales_data_for_period(db_session, start_date, end_date, group_by_dimension)` pour récupérer les données de ventes agrégées.
        *   **`db/cruds/clients_crud.py`**: Contient `get_client_acquisition_data(self, start_date, end_date, group_by_dimension, conn)` pour les statistiques d'acquisition de clients.
        *   **`db/cruds/products_crud.py`**: Contient `get_product_data_for_reporting(self, start_date, end_date, group_by_dimension, conn)` pour les analyses de produits.
    *   **`db/cruds/hr_reports_crud.py`**: CRUD spécifique pour des rapports RH (non modifié dans cette phase).
    *   **`db/cruds/report_configurations_crud.py`**: Pourrait stocker des configurations de rapports sauvegardées par les utilisateurs (non implémenté dans cette phase).

*   **Types de Rapports et Visualisations**:
    *   **Tableaux de Données**: Affichage tabulaire des données avec options de tri et de filtrage (standard dans `StatisticsDashboard` et personnalisable dans `AdvancedReportingTool`).
    *   **Graphiques (via `StatisticsDashboard` et `AdvancedReportingTool`)**: Utilisation de Matplotlib intégré à PyQt pour visualiser les données sous forme de :
        *   Graphiques linéaires (tendances).
        *   Graphiques à barres (comparaisons).
        *   Graphiques circulaires (proportions).
        *   Carte choroplèthe interactive des clients (via Folium et QWebEngineView dans `StatisticsDashboard`).
    *   **Tableaux de Bord Personnalisables**:
        *   Le `StatisticsDashboard` offre une vue d'ensemble avec des statistiques clés (KPIs, tendances, santé commerciale) et des segmentations prédéfinies (par pays, ville, statut, catégorie, popularité produit).
        *   L'**Outil de Reporting Avancé (`AdvancedReportingTool`)** intégré au `StatisticsDashboard` permet une personnalisation plus poussée :
            *   Sélection de plages de dates personnalisées.
            *   Choix du type de données à analyser (Ventes, Clients, Produits).
            *   Regroupement des données selon différentes dimensions (ex: ventes par mois/année/client/produit, clients par pays/ville/statut/date, produits par catégorie/nombre de ventes/chiffre d'affaires).
            *   Affichage des résultats sous forme de tableau dynamique.
            *   Génération de graphiques (barres, lignes, secteurs) basés sur les données sélectionnées et le type de graphique choisi.

*   **Fonctionnalités des Rapports**:
    *   **Filtrage Dynamique**:
        *   Le `StatisticsDashboard` offre des filtrages implicites par ses vues de segmentation et potentiellement des filtres globaux (non détaillés ici).
        *   L'`AdvancedReportingTool` permet un filtrage explicite par plage de dates, type de données et dimension de regroupement.
    *   **Exportation (via `AdvancedReportingTool`)**:
        *   Exporter les données tabulaires des rapports personnalisés aux formats CSV et Excel (utilisant `pandas`).
        *   Exporter les graphiques générés en tant qu'images (PNG, JPG, SVG via Matplotlib).
    *   **Sauvegarde de Configurations de Rapports**: (Potentiel futur) Permettre aux utilisateurs de sauvegarder leurs filtres et configurations de rapports favoris pour une réutilisation rapide.
    *   **Planification de Rapports (Potentiel Avancé)**: Envoi automatique de rapports par e-mail à des intervalles réguliers (non implémenté).

*   **Interaction avec la Base de Données**:
    *   Les fonctions CRUD dédiées dans `proforma_invoices_crud.py`, `clients_crud.py`, et `products_crud.py` effectuent les agrégations et filtrages nécessaires pour l'outil de reporting avancé.
    *   Le `StatisticsDashboard` utilise diverses fonctions CRUD et des requêtes directes pour afficher les statistiques globales et les segmentations.
    *   Des vues matérialisées ou des tables de résumé pourraient être utilisées en base de données pour optimiser la performance de certains rapports fréquemment consultés (non implémenté).

## 3. Flux de Travail Typique

### 3.1. Consultation d'un Rapport Standard / Tableau de Bord Global

1.  L'utilisateur navigue vers le `StatisticsDashboard` (potentiellement via `StatisticsPageWidget`).
2.  Le tableau de bord affiche des KPIs, des graphiques de segmentation (ex: clients par statut, carte des clients), et des tendances.
3.  Les données sont récupérées via les fonctions CRUD existantes et les nouvelles fonctions d'agrégation.
4.  L'utilisateur peut interagir avec la carte (cliquer sur un pays/client) ou rafraîchir les données.

### 3.2. Création d'un Rapport Personnalisé via l'Outil de Reporting Avancé

1.  Depuis le `StatisticsDashboard`, l'utilisateur accède à l'`AdvancedReportingTool`.
2.  Il sélectionne :
    *   Une plage de dates.
    *   Un type de données (Ventes, Clients, Produits).
    *   Une dimension de regroupement appropriée au type de données.
    *   Un type de graphique (Barres, Lignes, Secteurs).
3.  L'utilisateur clique sur "Générer Rapport".
4.  L'`AdvancedReportingTool` appelle la fonction CRUD correspondante (ex: `get_sales_data_for_period`) avec les paramètres sélectionnés.
5.  Les données agrégées sont retournées et affichées dans le tableau de résultats.
6.  Un graphique est généré dynamiquement à partir des mêmes données et affiché.
7.  L'utilisateur peut exporter les données du tableau (CSV/Excel) ou le graphique (image).

## 4. Interactions avec d'Autres Modules

*   **Tous les modules métier**: Le module de Rapports et Statistiques puise ses données de tous les autres modules qui gèrent des données opérationnelles :
    *   [Gestion des Clients](./module_gestion_clients.md) (Clients, Pays, Villes, Statuts)
    *   [Gestion des Produits](./module_gestion_produits.md) (Produits, Catégories)
    *   [Facturation et Paiements](./module_facturation_paiements.md) (Factures Proforma, Items de Facture)
    *   [Gestion de Projet](./module_gestion_projet.md)
    *   [Recrutement](./module_recrutement.md)
    *   [Gestion des Actifs/Inventaire](./module_gestion_actifs.md)
    *   Module RH (Employés, Congés, Performance - si ces données sont incluses dans les rapports).
*   **Base de Données**: Source principale de toutes les données pour les rapports. Les fonctions CRUD accèdent directement à la base de données SQLite.
*   **API Backend (`api/reports.py`)**: Son rôle peut être plus axé sur des rapports complexes ou des tâches de fond si l'UI gère directement les requêtes simples via les CRUDs.
*   **Gestion des Documents**: Pour l'exportation des rapports au format PDF (fonctionnalité d'exportation de rapport complet non implémentée dans cette phase pour l'outil avancé, mais existe potentiellement ailleurs).
*   **Gestion des E-mails**: Potentiellement pour l'envoi planifié de rapports.

## 5. Points d'Attention

*   **Performance**: La génération de rapports, surtout avec l'outil avancé permettant des requêtes sur de larges plages de dates, peut être gourmande. Les requêtes SQL dans les fonctions CRUD doivent être optimisées. L'utilisation d'index en base de données est cruciale. Pour de très grands volumes, des traitements asynchrones ou des mécanismes de cache pourraient être nécessaires.
*   **Exactitude des Données**: Les rapports ne sont utiles que si les données sous-jacentes sont exactes et à jour.
*   **Pertinence des Indicateurs**: Les options de regroupement et les types de données offerts dans l'outil avancé doivent correspondre à des besoins d'analyse pertinents.
*   **Flexibilité et Personnalisation**: L'outil de reporting avancé offre un bon niveau de personnalisation. La sauvegarde de configurations est une amélioration future possible.
*   **Sécurité et Accès aux Données**: Actuellement, l'accès aux données n'est pas restreint par utilisateur dans les fonctions CRUD de reporting. Si des rôles et permissions sont implémentés, ils devront être pris en compte.
*   **Clarté des Visualisations**: Les graphiques et tableaux doivent être clairs. Matplotlib offre de nombreuses options de personnalisation pour améliorer la lisibilité.
*   **Dépendances Externes**: L'outil de reporting avancé introduit une dépendance à `pandas` et `openpyxl` pour les exportations CSV/Excel. Celles-ci doivent être gérées.
*   **Gestion des Erreurs**: Une gestion robuste des erreurs (données vides, erreurs de base de données, erreurs d'exportation) est importante pour l'expérience utilisateur.

[end of cahier/desktop/module_rapports_statistiques.md]
