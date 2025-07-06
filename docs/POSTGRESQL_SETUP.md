# Configuration de PostgreSQL pour LEO ERP

Ce document explique comment configurer LEO ERP pour utiliser une base de données PostgreSQL au lieu de la base de données SQLite par défaut.

## Prérequis

1.  **Instance PostgreSQL** : Vous devez avoir une instance PostgreSQL en cours d'exécution et accessible. Vous pouvez l'installer localement, utiliser un service managé ou la lancer via Docker (voir ci-dessous pour un exemple avec Docker Compose pour le développement/test).
2.  **Pilote `psycopg2`** : Assurez-vous que le pilote `psycopg2-binary` est installé dans votre environnement Python. Il est inclus dans `requirements.txt`.
    ```bash
    pip install psycopg2-binary
    ```

## Configuration de l'Application

1.  **Accéder aux Paramètres** :
    *   Lancez LEO ERP.
    *   Allez dans le menu `Fichier` > `Paramètres`.
    *   Naviguez vers l'onglet `Données & Sauvegarde`.

2.  **Configurer le Type de Base de Données** :
    *   Dans la section "Configuration de la Base de Données", sélectionnez `PostgreSQL (experimental)` dans le menu déroulant "Type de Base de Données".
    *   Les champs spécifiques à PostgreSQL apparaîtront.

3.  **Remplir les Détails de Connexion PostgreSQL** :
    *   **Hôte PostgreSQL** : L'adresse de votre serveur PostgreSQL (ex: `localhost`, `192.168.1.100`, ou l'adresse de votre service cloud).
    *   **Port PostgreSQL** : Le port sur lequel PostgreSQL écoute (par défaut : `5432`).
    *   **Utilisateur PostgreSQL** : Le nom d'utilisateur pour se connecter à la base de données.
    *   **Mot de Passe PostgreSQL** : Le mot de passe associé à l'utilisateur.
    *   **Nom de la Base de Données PostgreSQL** : Le nom de la base de données que LEO ERP utilisera. *Cette base de données doit exister sur le serveur PostgreSQL.*
    *   **Mode SSL PostgreSQL** : Choisissez le mode de connexion SSL souhaité (`disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`). Pour les connexions locales non sécurisées, `disable` ou `prefer` peuvent convenir. Pour la production, `require` ou supérieur est recommandé.
    *   **Chemins des certificats SSL** (optionnel, dépend du mode SSL) :
        *   **SSL Root CA**: Chemin vers le fichier du certificat de l'autorité de certification racine.
        *   **SSL Client Cert**: Chemin vers le fichier du certificat client SSL.
        *   **SSL Client Key**: Chemin vers le fichier de la clé privée du client SSL.

4.  **Sauvegarder et Redémarrer** :
    *   Cliquez sur "Sauvegarder Tous les Paramètres".
    *   Redémarrez l'application LEO ERP pour que les changements prennent effet.

## Initialisation de la Base de Données et Migrations

Au premier démarrage avec la configuration PostgreSQL, l'application tentera :
1.  De se connecter à la base de données spécifiée.
2.  D'appliquer les migrations de schéma nécessaires via Alembic pour créer toutes les tables requises.

Assurez-vous que l'utilisateur PostgreSQL configuré a les droits suffisants pour créer des tables et potentiellement d'autres objets dans la base de données spécifiée.

## Exemple avec Docker Compose (pour Développement/Test)

Si vous souhaitez lancer une instance PostgreSQL rapidement pour le développement ou les tests, vous pouvez utiliser le fichier `docker-compose.yml` fourni à la racine du projet :

```bash
docker-compose up -d postgres_test_db
```

Cela démarrera un conteneur PostgreSQL avec les informations d'identification suivantes (par défaut) :
*   **Hôte**: `localhost` (car le port 5433 est mappé)
*   **Port**: `5433` (sur votre machine hôte)
*   **Utilisateur**: `testuser`
*   **Mot de passe**: `testpassword`
*   **Base de données**: `testdb_app`

Vous pouvez ensuite utiliser ces informations dans les paramètres de LEO ERP.

## Dépannage

*   **Erreur `psycopg2.OperationalError: connection to server at ... failed: Connection refused`**:
    *   Vérifiez que votre serveur PostgreSQL est en cours d'exécution.
    *   Vérifiez que l'hôte et le port sont corrects.
    *   Vérifiez que PostgreSQL est configuré pour accepter les connexions TCP/IP sur l'interface réseau attendue (souvent configuré dans `postgresql.conf` et `pg_hba.conf`).
    *   Vérifiez les pare-feu.
*   **Erreur d'authentification (FATAL: password authentication failed for user "...")**:
    *   Vérifiez que le nom d'utilisateur et le mot de passe sont corrects.
    *   Vérifiez la configuration de `pg_hba.conf` pour autoriser la méthode d'authentification pour l'utilisateur et l'adresse IP.
*   **Erreur `database "..." does not exist`**:
    *   Assurez-vous que la base de données spécifiée a bien été créée sur le serveur PostgreSQL avant de lancer l'application. LEO ERP appliquera les migrations mais ne créera pas la base de données elle-même.
*   **Problèmes SSL**:
    *   Assurez-vous que les chemins vers les fichiers de certificat/clé sont corrects et que les fichiers sont lisibles par l'application.
    *   Vérifiez que le serveur PostgreSQL est configuré pour le mode SSL que vous avez choisi.

Si vous rencontrez d'autres problèmes, consultez les logs de l'application (`client_manager_app.log`) pour des messages d'erreur plus détaillés.
