# Spécifications de l'API RESTful (FastAPI)

Ce document décrit les spécifications de l'API RESTful fournie par le serveur FastAPI intégré à l'application de bureau Client Document Manager. Cette API est principalement destinée à être consommée par l'application mobile compagnon, mais peut également servir à d'autres intégrations.

## 1. URL de Base

L'API est généralement accessible via l'adresse IP et le port sur lequel l'application de bureau (et donc le serveur FastAPI) est en cours d'exécution. Par exemple :

`http://<adresse_ip_serveur>:<port_serveur>/api/v1`

Le port par défaut pour FastAPI avec Uvicorn est souvent 8000 ou un autre port configuré dans `main.py` ou `api/main.py`. Le préfixe `/api/v1` est une convention courante pour versionner l'API.

## 2. Authentification

Toutes les requêtes (ou la plupart, à l'exception peut-être d'un endpoint de statut) devraient nécessiter une authentification pour des raisons de sécurité.

*   **Méthode**: Authentification basée sur les tokens (Bearer Token).
    1.  Un endpoint d'authentification (ex: `/auth/token`) prendra un nom d'utilisateur et un mot de passe.
    2.  En cas de succès, il retournera un token JWT (JSON Web Token) ou un token opaque.
    3.  Ce token devra être inclus dans l'en-tête `Authorization` de toutes les requêtes subséquentes :
        `Authorization: Bearer <votre_token>`
*   Les détails de l'implémentation de l'authentification se trouvent dans `api/auth.py` et utilisent probablement OAuth2PasswordBearer de FastAPI.

## 3. Formats de Données

*   **Requêtes**: Le corps des requêtes (pour POST, PUT, PATCH) doit être au format JSON.
*   **Réponses**: Les réponses du serveur seront au format JSON, sauf pour les téléchargements de fichiers (ex: PDF) où le `Content-Type` approprié sera utilisé (ex: `application/pdf`).
*   **Encodage**: UTF-8.

## 4. Conventions Générales

*   **Méthodes HTTP**: Utilisation standard des verbes HTTP :
    *   `GET`: Pour récupérer des ressources.
    *   `POST`: Pour créer de nouvelles ressources.
    *   `PUT`: Pour mettre à jour intégralement une ressource existante.
    *   `PATCH`: Pour mettre à jour partiellement une ressource existante.
    *   `DELETE`: Pour supprimer une ressource.
*   **Codes de Statut HTTP**: Utilisation des codes de statut HTTP standard pour indiquer le résultat des requêtes (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error, etc.).
*   **Pagination**: Pour les endpoints retournant des listes de ressources, la pagination sera implémentée (ex: via les paramètres de requête `skip` et `limit`).
*   **Filtrage et Tri**: Des paramètres de requête pourront être disponibles pour filtrer et trier les résultats.

## 5. Endpoints de l'API (Exemples Basés sur l'Analyse)

La liste suivante est une estimation des endpoints probables basée sur la structure du code (`api/`) et les besoins de l'application mobile. Chaque endpoint devrait être défini plus en détail avec ses paramètres, son corps de requête (si applicable), et ses réponses possibles.

---

### 5.1. Authentification (`api/auth.py`)

*   **`POST /auth/token`**
    *   **Description**: Authentifie l'utilisateur et retourne un token d'accès.
    *   **Corps de la Requête**: `application/x-www-form-urlencoded` (typique pour OAuth2PasswordRequestForm)
        *   `username` (str): Nom d'utilisateur.
        *   `password` (str): Mot de passe.
    *   **Réponse (200 OK)**:
        ```json
        {
          "access_token": "string",
          "token_type": "bearer"
        }
        ```
    *   **Réponses d'Erreur**: 400, 401.

*   **`GET /auth/users/me`**
    *   **Description**: Récupère les informations de l'utilisateur actuellement authentifié.
    *   **Réponse (200 OK)**: Modèle Pydantic de l'utilisateur (excluant le mot de passe).
    *   **Réponses d'Erreur**: 401.

---

### 5.2. Gestion des Produits (`api/products.py`)

*   **`GET /products/`**
    *   **Description**: Récupère une liste de produits.
    *   **Paramètres de Requête**: `skip` (int, optionnel), `limit` (int, optionnel), autres filtres (ex: `category`, `search_term`).
    *   **Réponse (200 OK)**: Liste d'objets produit.
        ```json
        [
          { "id": 1, "name": "Produit A", "reference": "REF001", "price": 100.0, ... },
          { "id": 2, "name": "Produit B", "reference": "REF002", "price": 150.0, ... }
        ]
        ```
    *   **Réponses d'Erreur**: 401.

*   **`GET /products/{product_id}`**
    *   **Description**: Récupère les détails d'un produit spécifique.
    *   **Paramètres de Chemin**: `product_id` (int).
    *   **Réponse (200 OK)**: Objet produit.
    *   **Réponses d'Erreur**: 401, 404.

---

### 5.3. Gestion des Documents (`api/documents.py` - à évaluer pour intégration "Gestion Client", `api/proformas.py`, etc.)

*   **`POST /documents/generate-proforma`** (Exemple, le nom exact peut varier)
    *   **Description**: Génère une facture proforma.
    *   **Corps de la Requête**: Données nécessaires pour la proforma (ID client, liste de produits avec quantités, langue, etc.).
        ```json
        {
          "client_id": 1,
          "language": "fr",
          "items": [
            { "product_id": 10, "quantity": 2 },
            { "product_id": 12, "quantity": 5 }
          ],
          ...
        }
        ```
    *   **Réponse (200 OK ou 201 Created)**:
        *   Option 1: Retourne le PDF directement (`Content-Type: application/pdf`).
        *   Option 2: Retourne un JSON avec un ID de document ou un lien pour télécharger le PDF.
            ```json
            {
              "document_id": "PRO2023-001",
              "status": "generated",
              "download_url": "/api/v1/documents/PRO2023-001/download"
            }
            ```
    *   **Réponses d'Erreur**: 400, 401, 404 (si client_id ou product_id non trouvé).

*   **`POST /documents/convert-html-to-pdf`**
    *   **Description**: Convertit un contenu HTML fourni en document PDF. Utilisé par l'application mobile.
    *   **Corps de la Requête**:
        ```json
        {
          "html_content": "<html><body><h1>Titre</h1><p>Contenu...</p></body></html>",
          "document_title": "Mon Document" // Optionnel
        }
        ```
    *   **Réponse (200 OK)**: Fichier PDF binaire (`Content-Type: application/pdf`).
    *   **Réponses d'Erreur**: 400, 401, 500 (si la conversion échoue).

*   **`GET /documents/{document_id}/download`**
    *   **Description**: Télécharge un document précédemment généré.
    *   **Paramètres de Chemin**: `document_id` (str ou int).
    *   **Réponse (200 OK)**: Fichier binaire du document (`Content-Type` approprié).
    *   **Réponses d'Erreur**: 401, 404.

---

### 5.4. Gestion des Modèles de Documents (`api/templates.py`)

*   **`GET /templates/`**
    *   **Description**: Récupère la liste des modèles de documents disponibles, potentiellement filtrable par type ou langue.
    *   **Paramètres de Requête**: `type` (str, optionnel), `language` (str, optionnel).
    *   **Réponse (200 OK)**: Liste d'objets modèle.
        ```json
        [
          { "id": 1, "name": "Proforma Standard FR", "type": "proforma", "language": "fr", ... },
          { "id": 2, "name": "Contrat de Vente EN", "type": "sales_contract", "language": "en", ... }
        ]
        ```
    *   **Réponses d'Erreur**: 401.

*   **`GET /templates/{template_id}/content`**
    *   **Description**: Récupère le contenu brut d'un modèle (ex: HTML pour les modèles mobiles).
    *   **Paramètres de Chemin**: `template_id` (int).
    *   **Réponse (200 OK)**: Contenu du modèle (`Content-Type: text/html` ou `application/json` encapsulant le contenu).
    *   **Réponses d'Erreur**: 401, 404.

---

### 5.5. Gestion des Clients (Simplifié pour l'API)

*   **`GET /clients/`**
    *   **Description**: Récupère une liste de clients (potentiellement simplifiée pour l'usage mobile).
    *   **Paramètres de Requête**: `skip`, `limit`, `search_term`.
    *   **Réponse (200 OK)**: Liste d'objets client (champs essentiels).
    *   **Réponses d'Erreur**: 401.

*   **`GET /clients/{client_id}`**
    *   **Description**: Récupère les détails d'un client spécifique.
    *   **Paramètres de Chemin**: `client_id` (int).
    *   **Réponse (200 OK)**: Objet client.
    *   **Réponses d'Erreur**: 401, 404.

---

### 5.6. Autres Endpoints Possibles

*   **Données de Configuration/Listes**:
    *   `GET /config/countries`: Liste des pays.
    *   `GET /config/languages`: Liste des langues supportées.
    *   `GET /config/payment-terms`: Termes de paiement.
*   **Employés/Utilisateurs (`api/employees.py`)**: Pour récupérer des listes d'employés si nécessaire pour l'assignation ou l'information.
*   **Notes et Activités**: Endpoints pour ajouter des notes ou consulter des activités liées à des clients ou projets.

## 6. Modèles de Données (Pydantic)

Chaque endpoint utilisant des corps de requête ou retournant des données structurées s'appuiera sur des modèles Pydantic pour la validation, la sérialisation et la désérialisation. Ces modèles sont généralement définis dans `api/models.py` ou directement dans les fichiers de routeurs.

Exemple de modèle Pydantic pour un produit (simplifié) :

```python
# Dans api/models.py ou products.py
from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    reference: Optional[str] = None
    price: float

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True # Pour la compatibilité avec les modèles SQLAlchemy
```

## 7. Documentation de l'API (Swagger/OpenAPI)

FastAPI génère automatiquement une documentation interactive de l'API (basée sur OpenAPI) qui est généralement disponible aux URLs :

*   `/docs`: Interface Swagger UI.
*   `/redoc`: Interface ReDoc.

Ces interfaces permettent de visualiser tous les endpoints, leurs paramètres, modèles de données, et même de les tester directement depuis le navigateur. Il est crucial que les modèles Pydantic et les docstrings des fonctions de route soient bien renseignés pour que cette documentation soit la plus utile possible.

---

Ce document fournit une base pour les spécifications de l'API. Chaque endpoint devrait être détaillé davantage avec tous les paramètres possibles, les codes de réponse exacts et les schémas de données précis lors de la phase de développement ou de documentation technique approfondie. L'exploration des fichiers dans `api/` du code source existant permettra de raffiner cette liste.
