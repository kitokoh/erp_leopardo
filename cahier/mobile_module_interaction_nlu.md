# Module : Interaction via NLU (Traitement du Langage Naturel)

Ce document détaille l'intégration et l'utilisation des fonctionnalités de Traitement du Langage Naturel (NLU) au sein de l'application mobile. L'objectif est de permettre aux utilisateurs d'interagir avec l'application en utilisant des commandes textuelles (et potentiellement vocales à l'avenir) en langage naturel.

## 1. Objectif Principal

Le module NLU vise à :
*   Interpréter les commandes en langage naturel fournies par l'utilisateur.
*   Identifier l'intention principale de l'utilisateur.
*   Extraire les informations pertinentes (entités) de la commande.
*   Traduire ces intentions et entités en actions concrètes que l'interface utilisateur (UI) de l'application peut exécuter.

## 2. Composants Clés

Le module NLU est principalement composé de deux fichiers dans le dossier `mobile/`:

*   **`nlu_handler.py`**: Responsable de l'analyse de bas niveau de la commande textuelle.
*   **`nlu_controller.py`**: Responsable de la transformation du résultat de l'analyse NLU en une action exécutable par l'UI.

Il n'utilise pas de moteur NLU externe ou de bibliothèque d'intelligence artificielle avancée. L'interprétation est basée sur des règles, des mots-clés et des expressions régulières.

## 3. Flux de Traitement d'une Commande NLU

1.  **Entrée Utilisateur**: L'utilisateur saisit une commande textuelle (par exemple, via un champ de saisie dans l'UI, ou potentiellement via une reconnaissance vocale transcrite en texte).

2.  **Analyse par `nlu_handler.parse_command(text: str)`**:
    *   La commande textuelle est passée à cette fonction.
    *   La fonction normalise le texte (le met en minuscules).
    *   Elle tente d'identifier une **intention** (l'action que l'utilisateur veut effectuer) en cherchant des mots-clés et des motifs spécifiques (par exemple, "générer pdf", "ajouter produit", "changer langue").
    *   Elle tente d'extraire des **entités** (les paramètres de l'action) en utilisant des expressions régulières et des listes prédéfinies (par exemple, extraire un nom de produit, une quantité, une adresse e-mail, un nom de langue).
        *   Listes prédéfinies dans `nlu_handler.py`: `SUPPORTED_LANGUAGES`, `SUPPORTED_COUNTRIES`, `SUPPORTED_TEMPLATES`.
    *   Elle retourne un dictionnaire structuré contenant `intent` (une chaîne) et `entities` (un dictionnaire d'entités). Si la commande n'est pas comprise, l'intention `UNKNOWN` est retournée.

3.  **Traitement par `nlu_controller.process_nlu_result(nlu_data: Dict[str, Any])`**:
    *   Le dictionnaire (`nlu_data`) issu de `nlu_handler.py` est passé à cette fonction.
    *   En fonction de l'`intent` et des `entities` présentes :
        *   La fonction détermine un `action_type` spécifique que l'UI peut comprendre (par exemple, `TRIGGER_PDF_GENERATION`, `ADD_UI_PRODUCT`, `UPDATE_UI_LANGUAGE`).
        *   Elle formate les données nécessaires pour cette action (par exemple, pour `ADD_UI_PRODUCT`, elle inclura `product_name` et `quantity`).
    *   Si l'intention n'est pas gérable, si des entités cruciales manquent, ou si l'intention est `UNKNOWN`, une action de type `NLU_ERROR` est retournée avec un message explicatif pour l'utilisateur.
    *   Elle retourne un dictionnaire `action` prêt à être consommé par la couche UI.

4.  **Exécution par l'UI**:
    *   La couche UI reçoit le dictionnaire `action`.
    *   En fonction de `action_type`, l'UI effectue l'opération correspondante (par exemple, appeler la méthode pour générer un PDF, mettre à jour un Spinner de langue, ajouter un produit à la liste de sélection).
    *   Si `action_type` est `NLU_ERROR` ou `DISPLAY_NLU_HELP`, l'UI affiche le message fourni à l'utilisateur.

## 4. Intentions et Entités Gérées (Exemples)

Basé sur `nlu_handler.py` et `nlu_controller.py` :

*   **Générer un PDF**:
    *   Intentions : `GENERATE_PDF`, `DISPLAY_PDF`
    *   Entités : Aucune spécifique pour la génération simple.
    *   Action UI : `TRIGGER_PDF_GENERATION`, `TRIGGER_PDF_DISPLAY`

*   **Envoyer un PDF par E-mail**:
    *   Intention : `EMAIL_PDF`
    *   Entités : `recipient` (adresse e-mail), `subject` (sujet de l'e-mail).
    *   Action UI : `TRIGGER_EMAIL_SENDING` avec les entités.

*   **Ajouter un Produit**:
    *   Intention : `ADD_PRODUCT`
    *   Entités : `product_name`, `quantity` (optionnelle, défaut à 1).
    *   Action UI : `ADD_UI_PRODUCT` avec nom et quantité.

*   **Sélectionner une Langue**:
    *   Intention : `SELECT_LANGUAGE`
    *   Entités : `language_name`.
    *   Action UI : `UPDATE_UI_LANGUAGE` avec le nom de la langue.

*   **Sélectionner un Pays**:
    *   Intention : `SELECT_COUNTRY`
    *   Entités : `country_name`.
    *   Action UI : `UPDATE_UI_COUNTRY` avec le nom du pays.

*   **Sélectionner un Modèle**:
    *   Intention : `SELECT_TEMPLATE`
    *   Entités : `template_name`.
    *   Action UI : `UPDATE_UI_TEMPLATE` avec le nom du modèle.

*   **Aide**:
    *   Intention : `HELP`
    *   Action UI : `DISPLAY_NLU_HELP` avec un message d'aide.

*   **Inconnu/Erreur**:
    *   Intention : `UNKNOWN` ou erreurs de traitement.
    *   Action UI : `NLU_ERROR` avec un message.

## 5. Limitations Actuelles

*   **Simplicité du Parsing**: L'analyse est basée sur des mots-clés et des expressions régulières simples. Elle peut être fragile face à des formulations complexes ou ambiguës.
*   **Pas de Contexte Conversationnel**: Chaque commande est traitée indépendamment. Le système ne se souvient pas des commandes précédentes.
*   **Vocabulaire Limité**: Les entités comme les noms de produits, langues, pays, modèles sont partiellement gérées par des listes prédéfinies ou des motifs génériques. L'ajout de nouveaux éléments (par exemple, de nouveaux noms de produits) nécessiterait une mise à jour de la logique de `nlu_handler.py` ou une stratégie d'extraction d'entités plus dynamique (par exemple, en interrogeant `mobile_data_api` pour les noms de produits valides).
*   **Pas de Véritable IA**: Il ne s'agit pas d'un système d'IA apprenant. Toute amélioration de la compréhension nécessite une modification manuelle du code.

## 6. Intégration à l'UI (Conceptuelle)

L'intégration à l'UI Kivy (par exemple, `DocumentGenerationScreen`) nécessiterait :
*   Un composant d'entrée de texte pour que l'utilisateur tape sa commande.
*   Un mécanisme pour envoyer ce texte à `nlu_handler.parse_command()`, puis le résultat à `nlu_controller.process_nlu_result()`.
*   Une logique dans `DocumentGenerationScreen` pour interpréter le dictionnaire `action` retourné et appeler les méthodes appropriées de l'UI (par exemple, `self.language_spinner.text = action['language_name']`, `self.on_generate_pdf_button_pressed(None)`).
*   Un espace pour afficher les messages d'erreur ou d'aide du NLU.
