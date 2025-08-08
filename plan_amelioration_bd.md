# Plan d'Amélioration de la Base de Données

## 1. Introduction

Ce document propose un plan d'action pour corriger les problèmes de conception identifiés dans le rapport d'analyse de la base de données. L'objectif est de refactoriser la base de données pour améliorer sa cohérence, sa performance, son intégrité et sa maintenabilité.

Le plan est divisé en phases pour permettre une mise en œuvre progressive.

## 2. Phase 1 : Corrections Structurelles Critiques (Haute Priorité)

Cette phase aborde les problèmes les plus graves qui affectent l'intégrité et la fonctionnalité de base de l'application.

### 2.1. Standardisation des Clés Primaires

*   **Action** : Modifier les modèles `User`, `Client`, et `Invoice` (et toute autre table utilisant une clé primaire non-entière) pour utiliser une clé primaire de type `Integer` auto-incrémentée.
*   **Exemple (`Client`)** :
    ```python
    # Avant
    # client_id = Column(String, primary_key=True)

    # Après
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String, unique=True, nullable=False, index=True) # Garder l'ancien ID comme identifiant unique
    ```
*   **Justification** : Améliore les performances des jointures, simplifie la gestion des clés et standardise l'architecture. Conserver l'ancien ID comme un identifiant métier unique et indexé assure la rétrocompatibilité si nécessaire.

### 2.2. Création des Tables Manquantes

*   **Action** : Créer les modèles SQLAlchemy pour les tables manquantes qui sont essentielles à la logique métier.
    *   **`ProductCategory`** : Créer une table `product_categories` avec `id` (PK) et `name` (unique).
    *   **`InvoiceLine`** : Créer une table `invoice_lines` avec `id` (PK), `invoice_id` (FK), `product_id` (FK), `quantity`, `unit_price`, `total_price`.
*   **Justification** : Permet d'établir une intégrité référentielle correcte et de mettre en œuvre des fonctionnalités critiques (catégorisation de produits, contenu des factures).

### 2.3. Correction des Clés Étrangères et Ajout des Relations

*   **Action** : Mettre à jour tous les modèles pour assurer que les clés étrangères et les relations ORM sont correctement définies.
    *   **`Product`** : Remplacer `category: String` par `category_id: ForeignKey` et ajouter `category = relationship("ProductCategory")`.
    *   **`Invoice`** :
        *   Corriger le type de `client_id` pour correspondre à la PK de `clients`.
        *   Ajouter `client = relationship("Client")`.
        *   Ajouter `lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")`.
    *   **`InvoiceLine`** : Ajouter `invoice = relationship("Invoice", back_populates="lines")` et `product = relationship("Product")`.
*   **Justification** : Exploite pleinement la puissance de l'ORM, simplifie les requêtes et garantit l'intégrité des données via les contraintes de la base de données. La cascade sur les lignes de facture assure que les lignes sont supprimées si la facture l'est.

## 3. Phase 2 : Amélioration de la Modélisation (Moyenne Priorité)

Cette phase se concentre sur l'amélioration de la structure des données pour les rendre plus exploitables et sur l'harmonisation des conventions.

### 3.1. Modélisation Structurée des Données

*   **Action** : Remplacer les champs `Text` contenant des données structurées par des modèles plus appropriés.
*   **Exemple (`Product.dimensions`)** :
    ```python
    # Avant
    # dimensions = Column(Text)

    # Après
    dimension_length = Column(Float)
    dimension_width = Column(Float)
    dimension_height = Column(Float)
    dimension_unit = Column(String, default='cm')
    ```
*   **Justification** : Permet la validation, l'indexation et l'interrogation efficace des données.

### 3.2. Harmonisation des Horodatages

*   **Action** : S'assurer que toutes les tables possèdent des colonnes `created_at` et `updated_at` et qu'elles sont gérées de manière cohérente par la base de données.
*   **Exemple (`Invoice`)** :
    ```python
    # Avant
    # created_at = Column(DateTime)
    # updated_at = Column(DateTime)

    # Après
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    ```
*   **Justification** : Garantit la fiabilité et la cohérence des métadonnées temporelles à travers toute l'application.

## 4. Recommandations pour la Migration

*   **Problème** : Les changements de schéma proposés ne sont pas rétrocompatibles. Ils nécessiteront une migration des données existantes.
*   **Recommandation** :
    1.  **Intégrer Alembic** : Alembic est l'outil de migration de schémas standard pour SQLAlchemy. Il faut l'initialiser dans le projet.
    2.  **Générer un Script de Migration** : Une fois les modèles corrigés, utiliser Alembic pour générer un script de migration.
    3.  **Écrire la Logique de Migration des Données** : Le script de migration auto-généré devra être modifié manuellement pour inclure la logique de migration des données (par exemple, créer les nouvelles clés primaires `Integer`, peupler les colonnes `client_id` uniques à partir des anciennes clés primaires, puis mettre à jour les clés étrangères dans les tables associées).
    4.  **Tester la Migration** : Tester rigoureusement la migration sur une copie de la base de données de production avant de l'appliquer.

Ce plan fournit une feuille de route pour transformer la base de données actuelle en une fondation robuste et fiable pour l'avenir de l'application.
