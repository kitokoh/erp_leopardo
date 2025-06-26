# Module : Synchronisation et Gestion des Données Mobiles

Ce document explique comment l'application mobile gère la récupération et l'envoi de données vers un système backend. Actuellement, cette gestion est simulée via le fichier `mobile/data_handler.py`, qui agit comme une couche d'accès à une API fictive.

## 1. Objectif Principal

L'objectif de ce module est de fournir à l'application mobile les données nécessaires à son fonctionnement (par exemple, listes de produits, modèles de documents, contexte client) et de transmettre des requêtes ou des données au backend (par exemple, HTML à convertir en PDF). Il centralise la logique de communication avec le backend.

## 2. Mode de Fonctionnement Actuel (Simulation d'API)

Le fichier `mobile/data_handler.py` ne met pas en œuvre de véritable synchronisation ou de stockage local persistant. Il contient une série de fonctions qui simulent des appels à des points de terminaison (endpoints) d'une API RESTful. Chaque fonction :
*   Affiche un message dans la console indiquant quel "appel API" est effectué.
*   Retourne des données statiques (codées en dur) ou légèrement dynamisées pour simuler une réponse du backend.

## 3. Fonctions Principales et Données Gérées

Les fonctions suivantes simulent la récupération ou l'envoi de données :

*   **`get_client_and_company_ids_from_api() -> Dict[str, str]`**:
    *   **API simulée**: `GET /api/mobile/context/ids`
    *   **Rôle**: Récupérer les identifiants d'un client par défaut et de l'entreprise par défaut.
    *   **Données retournées (mock)**: `{ 'client_id': 'mock_client_123', 'company_id': 'mock_company_abc' }`

*   **`get_document_context_data_from_api(...) -> Optional[dict]`**:
    *   **API simulée**: `POST /api/mobile/context/document_data`
    *   **Rôle**: Obtenir un ensemble complet de données (contexte) nécessaires pour remplir un modèle de document.
    *   **Paramètres**: ID client, ID entreprise, code langue, liste des produits sélectionnés avec quantité, contexte additionnel.
    *   **Données retournées (mock)**: Dictionnaire contenant des informations sur le client, l'entreprise, les produits, la langue, le pays, etc.

*   **`get_all_products_for_selection_from_api(language_code: str, name_pattern: Optional[str]) -> List[Dict]`**:
    *   **API simulée**: `GET /api/mobile/products?lang={language_code}&search={name_pattern}`
    *   **Rôle**: Récupérer la liste des produits disponibles pour la sélection, potentiellement filtrée par langue et un motif de nom.
    *   **Données retournées (mock)**: Une liste de dictionnaires, chaque dictionnaire représentant un produit avec son ID, nom, prix, description.

*   **`get_all_countries_from_api() -> List[Dict]`**:
    *   **API simulée**: `GET /api/mobile/countries`
    *   **Rôle**: Récupérer la liste des pays.
    *   **Données retournées (mock)**: Une liste de dictionnaires, chaque dictionnaire représentant un pays avec ID, nom, devise.

*   **`get_document_templates_from_api(category_name: Optional[str]) -> List[Dict]`**:
    *   **API simulée**: `GET /api/mobile/templates?category={category_name}`
    *   **Rôle**: Récupérer la liste des modèles de documents disponibles, potentiellement filtrée par catégorie.
    *   **Données retournées (mock)**: Une liste de dictionnaires, chaque dictionnaire représentant un modèle avec ID, nom, code langue, catégorie, nom de fichier de base.

*   **`get_template_content_from_api(template_id: str) -> Optional[str]`**:
    *   **API simulée**: `GET /api/mobile/templates/{template_id}/content`
    *   **Rôle**: Récupérer le contenu HTML brut d'un modèle de document spécifique.
    *   **Données retournées (mock)**: Une chaîne de caractères contenant du HTML.

*   **`convert_html_to_pdf_api(html_content: str, base_url: Optional[str]) -> Optional[bytes]`**:
    *   **API simulée**: `POST /api/mobile/pdf/convert`
    *   **Rôle**: Envoyer du contenu HTML au backend pour qu'il soit converti en PDF.
    *   **Paramètres**: Le contenu HTML et une URL de base optionnelle pour résoudre les ressources relatives (images, CSS).
    *   **Données retournées (mock)**: Des octets simulant le contenu d'un fichier PDF.

*   **`get_languages_from_api() -> List[Dict]`**:
    *   **API simulée**: `GET /api/mobile/languages`
    *   **Rôle**: Récupérer la liste des langues supportées par l'application (pour les traductions de contenu, etc.).
    *   **Données retournées (mock)**: Une liste de dictionnaires, chaque dictionnaire représentant une langue avec son code et son nom.

*   **`get_mobile_temp_dir() -> str`** et **`get_mobile_templates_dir() -> str`**:
    *   Ces fonctions ne simulent pas des appels API mais fournissent des chemins de répertoires locaux.
    *   `get_mobile_temp_dir()`: Retourne un chemin vers un répertoire temporaire pour stocker, par exemple, les PDF générés. Actuellement, crée un sous-dossier `mobile_temp_docs`.
    *   `get_mobile_templates_dir()`: Placeholder retournant un chemin fictif pour les modèles sur mobile. En pratique, les modèles seraient probablement inclus dans le package de l'application ou récupérés via API.

## 4. Communication et Dépendances

*   L'ensemble des fonctionnalités de l'application mobile (interface utilisateur, génération de documents) dépend de ce module pour obtenir les données nécessaires.
*   Ce module dépend entièrement d'une API backend (actuellement simulée) pour toutes les opérations de données.
*   Il n'y a **pas de stockage de données local persistant** implémenté dans ce module. Toutes les données sont récupérées "à la volée" à chaque appel de fonction (simulé).

## 5. Stratégie de Synchronisation (Future)

Pour une application réelle, une stratégie de synchronisation plus robuste serait nécessaire. Elle pourrait inclure :

*   **Mise en Cache Locale**: Stocker certaines données fréquemment consultées (ex: liste de produits, modèles) localement sur l'appareil pour améliorer les performances et permettre une utilisation hors ligne limitée.
*   **Synchronisation Périodique ou sur Demande**: Mettre à jour les données locales avec le backend.
*   **Gestion des Conflits**: Si des données peuvent être modifiées localement et sur le serveur.
*   **Indicateurs de Statut de Synchronisation**: Informer l'utilisateur de l'état de la synchronisation.

Actuellement, l'application mobile nécessite une connexion réseau fonctionnelle pour toutes les opérations impliquant des données, car chaque action déclenche un "appel API".
