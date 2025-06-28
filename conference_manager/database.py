import sqlite3
from sqlite3 import Error
import os

# Définir le chemin de la base de données. Par exemple, dans le répertoire du module.
# Ou, pour une application plus large, cela pourrait être dans un répertoire de données utilisateur.
DATABASE_NAME = "conference_manager.db"
# Pour les tests, on pourra passer ":memory:" ou un autre nom de fichier.

_memory_conn = None # Variable globale pour la connexion en mémoire partagée

def get_db_connection(db_name: str = DATABASE_NAME):
    """
    Crée une connexion à la base de données SQLite.
    Si db_name est ":memory:", une base de données en mémoire partagée est utilisée.
    """
    global _memory_conn
    conn = None
    try:
        if db_name == ":memory:":
            if _memory_conn is None:
                # print("DEBUG DB: _memory_conn is None, création nouvelle connexion :memory:")
                _memory_conn = sqlite3.connect(":memory:")
                _memory_conn.row_factory = sqlite3.Row
                # print(f"DEBUG DB: Nouvelle connexion :memory: créée (id: {id(_memory_conn)})")
            # else:
                # print(f"DEBUG DB: Réutilisation connexion :memory: (id: {id(_memory_conn)})")
            return _memory_conn
        else:
            # Connexion à un fichier de base de données
            # print(f"DEBUG DB: Création/ouverture connexion fichier: {db_name}")
            db_path = os.path.abspath(db_name)
            # os.makedirs(os.path.dirname(db_path), exist_ok=True) # Décommenter si nécessaire
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
    except Error as e:
        print(f"Erreur de connexion à la base de données SQLite '{db_name}': {e}")
    return None # Retourne None en cas d'erreur de connexion à un fichier

def close_all_connections():
    """Ferme la connexion en mémoire partagée si elle est ouverte."""
    global _memory_conn
    if _memory_conn:
        # print("DEBUG: Fermeture connexion :memory:")
        _memory_conn.close()
        _memory_conn = None

def create_tables(conn: sqlite3.Connection, drop_first: bool = False):
    """
    Crée les tables dans la base de données SQLite.
    Si drop_first est True, supprime les tables avant de les recréer.
    """
    # print(f"DEBUG DB create_tables: conn id: {id(conn)}, name: {'in-memory' if conn == _memory_conn else 'fichier'}, drop_first: {drop_first}")
    cursor = conn.cursor()

    if drop_first:
        cursor.execute("DROP TABLE IF EXISTS conferences")
        cursor.execute("DROP TABLE IF EXISTS clients")
        # print("DEBUG DB: Tables 'conferences' et 'clients' supprimées (si elles existaient).")

    sql_create_clients_table = """
    CREATE TABLE IF NOT EXISTS clients (
        id TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        coordonnees TEXT -- Stockera du JSON
    );
    """

    sql_create_conferences_table = """
    CREATE TABLE IF NOT EXISTS conferences (
        id TEXT PRIMARY KEY,
        titre TEXT NOT NULL,
        date_heure_creation TIMESTAMP NOT NULL,
        date_heure_programmation TIMESTAMP,
        notes_rapport TEXT,
        client_id TEXT,
        participants_externes TEXT,
        statut TEXT NOT NULL,
        lieu TEXT,
        description_calendrier TEXT,
        rappel_active BOOLEAN NOT NULL DEFAULT 1,
        minutes_rappel_avant INTEGER,
        utilisateur_id TEXT,
        duree_minutes INTEGER,
        FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE SET NULL
        -- Pas de clé étrangère pour utilisateur_id pour l'instant, car pas de table utilisateurs dédiée
    );
    """
    try:
        cursor.execute(sql_create_clients_table)
        cursor.execute(sql_create_conferences_table)
        conn.commit()
        # print("DEBUG DB: Tables 'clients' et 'conferences' créées (si elles n'existaient pas ou après drop).")
    except Error as e:
        print(f"Erreur lors de la création des tables: {e}")

def init_db(db_name: str = DATABASE_NAME, drop_tables_for_test: bool = False):
    """Initialise la base de données: crée la connexion et les tables."""
    conn = get_db_connection(db_name)
    if conn:
        create_tables(conn, drop_first=drop_tables_for_test) # Passer le paramètre ici
        # Si init_db a créé une connexion fichier (pas _memory_conn), elle doit être fermée.
        # _memory_conn est gérée par close_all_connections() à la fin des tests.
        if db_name != ":memory:" and conn is not _memory_conn:
            conn.close()
        # Les print ont été commentés pour réduire la verbosité des logs de test
    else:
        # Gérer l'échec de l'initialisation si nécessaire
        print(f"ALERTE: Échec de l'obtention d'une connexion pour init_db avec '{db_name}'")
        pass


# Exemple d'utilisation (peut être appelé une fois au démarrage de l'application principale)
if __name__ == '__main__':
    # Pour un test rapide de ce module
    db_test_file = "test_conference_manager.db"
    if os.path.exists(db_test_file):
        os.remove(db_test_file)

    init_db(db_name=db_test_file)

    # Test avec base de données en mémoire
    init_db(db_name=":memory:")

    # Vérification simple: essayer de se connecter et d'insérer une donnée (optionnel ici)
    conn_test = get_db_connection(db_test_file)
    if conn_test:
        print(f"Connexion à '{db_test_file}' réussie.")
        # Vous pouvez ajouter un petit test d'insertion/sélection ici si vous le souhaitez
        conn_test.close()

    if os.path.exists(db_test_file):
        os.remove(db_test_file) # Nettoyage après le test
        print(f"Fichier de base de données de test '{db_test_file}' supprimé.")
