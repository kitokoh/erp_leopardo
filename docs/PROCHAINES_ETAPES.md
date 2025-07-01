# Proposition pour les Prochaines Étapes de Développement

Ce document détaille les prochaines étapes envisagées pour le développement de l'application, basées sur le résumé des travaux effectués et des points restants.

## Objectif Principal de la Prochaine Phase
Stabiliser les fonctionnalités clés du workflow client, améliorer l'expérience utilisateur pour la génération de documents, et commencer à adresser les améliorations fonctionnelles plus larges.

## Tâches Prioritaires

1.  **Finalisation et Test du Workflow d'Ajout Client Complet :**
    *   **Modale 3 (Ajout Produit au Client) - Amélioration Cruciale :**
        *   **Objectif**: Permettre d'ajouter un *nouveau produit* directement depuis cette modale.
        *   **Détails**:
            *   Le produit créé doit être ajouté au client actuel.
            *   Le produit créé doit également être ajouté à la base de données globale des produits (visible et gérable dans le module "Product Management").
            *   S'assurer que la sélection d'un produit existant et son ajout au client fonctionnent toujours correctement.
        *   **Fichiers concernés**: `dialogs/product_dialog.py`, `document_manager_logic.py`, potentiellement `db/cruds/products_crud.py` et `db/cruds/client_project_products_crud.py`.
    *   **Test de Bout en Bout**: Effectuer un test complet du workflow "Ajouter un nouveau client" (depuis le bouton dans "Gestion Documents") en incluant la création de contact, l'ajout/création de produit (avec la nouvelle amélioration), et la génération de document via la Modale 4 (`CreateDocumentDialog`).

2.  **Implémentation de la Logique de Génération de Documents (`_generate_document` dans `CreateDocumentDialog`)** :
    *   **Objectif**: Remplacer les placeholders actuels par une logique de génération fonctionnelle pour les types de documents principaux (HTML, DOCX, et jeter les bases pour XLSX).
    *   **Détails**:
        *   **HTML**: Utiliser `HtmlEditor.populate_html_content` (déjà en place).
        *   **DOCX**: Utiliser `utils.populate_docx_template` (déjà en place).
        *   **XLSX**: Rechercher/Implémenter une solution pour populer des modèles Excel. Cela pourrait impliquer l'utilisation d'une bibliothèque comme `openpyxl` pour lire un modèle `.xlsx`, populer les cellules basées sur le `document_context`, et sauvegarder le nouveau fichier. Créer un fichier `excel_generation.py` ou ajouter à `document_utils.py`.
        *   S'assurer que les `template_type_filter` dans `DOCUMENT_TYPE_MAPPING` correspondent aux `template_type` réels dans la base de données pour les modèles HTML, DOCX, et futurs XLSX.
    *   **Fichiers concernés**: `dialogs/create_document_dialog.py`, (nouveau) `excel_generation.py` ou `document_utils.py`.

3.  **Configuration Dynamique des Types de Documents (`CreateDocumentDialog`)** :
    *   **Objectif**: Remplacer le `DOCUMENT_TYPE_MAPPING` codé en dur par un système dynamique.
    *   **Approche suggérée**:
        *   Introduire une nouvelle table en base de données (ex: `DocumentGenerationTypes`) ou étendre `TemplateCategories` pour stocker les types de documents générables (ex: "Devis", "Facture Proforma"), leur `template_type_filter` associé (ex: "DEVIS_HTML"), et potentiellement l'extension de fichier attendue.
        *   Modifier `_load_document_types_and_languages` pour peupler `doc_type_combo` à partir de cette source.
    *   **Fichiers concernés**: `dialogs/create_document_dialog.py`, `db/init_schema.py`, `db/cruds/` (nouveau CRUD ou modifié).

## Tâches Secondaires (à aborder si le temps le permet ou lors d'une phase ultérieure)

4.  **Revue et Finalisation des Icônes et de `icons_rc.py`** :
    *   Identifier toutes les icônes manquantes ou mal affichées dans l'application.
    *   S'assurer que toutes les icônes sont correctement référencées dans `icons.qrc`.
    *   Regénérer `icons_rc.py` (`pyrcc5 icons.qrc -o icons_rc.py`) et s'assurer qu'il est inclus correctement.

5.  **Documents par Défaut au Premier Lancement (`app_setup.py`)** :
    *   Vérifier et tester la logique dans `app_setup.initialize_default_templates()` pour s'assurer que les modèles de base (HTML, Excel si applicable) sont créés dans les bons dossiers (`templates/<lang_code>/`) lors du premier lancement.

6.  **Affichage Détails Client (Revue `ClientWidget`)** :
    *   Revoir le rafraîchissement des données dans `ClientWidget` pour s'assurer que toutes les informations affichées sont à jour après des modifications (ex: via `EditClientDialog` ou actions dans les onglets).

7.  **Session Utilisateur ("Se souvenir de moi") - Tests Approfondis** :
    *   Tester en profondeur la fonctionnalité "Se souvenir de moi" sur différentes sessions, après fermeture/redémarrage, et après déconnexion manuelle.

## Points à Plus Long Terme / Moins Prioritaires

*   Intégration d'une bibliothèque de génération Excel plus avancée si `openpyxl` s'avère limité pour des modèles complexes.
*   Amélioration de la gestion des erreurs et des notifications utilisateur.
*   Développement de tests unitaires et d'intégration.
*   Investigation des avertissements et erreurs non bloquants (PyAudio, API job-openings, GLib-GIO, StatisticsDashboard layout).

## Prochaine Action Immédiate
Commencer par la **Tâche Prioritaire 1 : Finalisation et Test du Workflow d'Ajout Client Complet**, en se concentrant sur l'amélioration de la Modale 3 (Ajout Produit).
```
