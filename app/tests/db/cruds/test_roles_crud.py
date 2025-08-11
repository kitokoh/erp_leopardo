import pytest
import sqlite3
from app.db.cruds import roles_crud
from app.db.connection import get_db_connection # Pourrait être mocké ou utilisé pour setup
from app.db.init_schema import initialize_database # Pour s'assurer que la table Roles existe

# Fixture pour initialiser une base de données en mémoire pour chaque test
@pytest.fixture
def db_conn():
    # Utilise une base de données en mémoire pour les tests
    # On pourrait aussi utiliser la DATABASE_PATH de config mais pointant vers un fichier de test
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row # Important pour que les résultats soient des dicts

    # Initialiser le schéma (au moins la table Roles)
    # Pour cela, on a besoin que initialize_database puisse prendre un chemin de connexion
    # ou qu'on exécute le SQL de création de table manuellement ici.
    # Temporairement, on va recréer la table Roles manuellement pour ce test.
    # Idéalement, initialize_database serait adaptable.
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    yield conn
    conn.close()

def test_add_role_success(db_conn):
    """Test adding a new role successfully."""
    role_name = "Test Role"
    description = "A role for testing"
    role_id = roles_crud.add_role(role_name, description, conn=db_conn)
    assert role_id is not None
    assert isinstance(role_id, int)

    # Vérifier que le rôle a été ajouté
    added_role = roles_crud.get_role_by_id(role_id, conn=db_conn)
    assert added_role is not None
    assert added_role["role_name"] == role_name
    assert added_role["description"] == description

def test_add_role_duplicate_name(db_conn):
    """Test adding a role with a name that already exists."""
    role_name = "Duplicate Role"
    roles_crud.add_role(role_name, "First instance", conn=db_conn)
    duplicate_role_id = roles_crud.add_role(role_name, "Second instance", conn=db_conn)
    assert duplicate_role_id is None # Should fail to add due to UNIQUE constraint

def test_get_role_by_id_exists(db_conn):
    """Test fetching an existing role by ID."""
    role_name = "Fetch Role ID"
    role_id = roles_crud.add_role(role_name, conn=db_conn)
    assert role_id is not None

    fetched_role = roles_crud.get_role_by_id(role_id, conn=db_conn)
    assert fetched_role is not None
    assert fetched_role["role_id"] == role_id
    assert fetched_role["role_name"] == role_name

def test_get_role_by_id_not_exists(db_conn):
    """Test fetching a non-existent role by ID."""
    fetched_role = roles_crud.get_role_by_id(99999, conn=db_conn) # Assuming 99999 does not exist
    assert fetched_role is None

def test_get_role_by_name_exists(db_conn):
    """Test fetching an existing role by name."""
    role_name = "Fetch Role Name"
    roles_crud.add_role(role_name, conn=db_conn)

    fetched_role = roles_crud.get_role_by_name(role_name, conn=db_conn)
    assert fetched_role is not None
    assert fetched_role["role_name"] == role_name

def test_get_role_by_name_not_exists(db_conn):
    """Test fetching a non-existent role by name."""
    fetched_role = roles_crud.get_role_by_name("NonExistentRole", conn=db_conn)
    assert fetched_role is None

def test_list_roles_empty(db_conn):
    """Test listing roles when no roles exist."""
    all_roles = roles_crud.list_roles(conn=db_conn)
    assert isinstance(all_roles, list)
    assert len(all_roles) == 0

def test_list_roles_with_data(db_conn):
    """Test listing roles when roles exist."""
    role1_name = "Admin Role"
    role2_name = "User Role"
    roles_crud.add_role(role1_name, conn=db_conn)
    roles_crud.add_role(role2_name, conn=db_conn)

    all_roles = roles_crud.list_roles(conn=db_conn)
    assert isinstance(all_roles, list)
    assert len(all_roles) == 2

    # Check if names are in the fetched list (order might vary depending on DB, but list_roles sorts by name)
    fetched_names = sorted([role["role_name"] for role in all_roles])
    assert fetched_names == sorted([role1_name, role2_name])

def test_add_role_without_description(db_conn):
    """Test adding a role with only a name (description is None)."""
    role_name = "NameOnly Role"
    role_id = roles_crud.add_role(role_name, conn=db_conn) # description defaults to None
    assert role_id is not None

    added_role = roles_crud.get_role_by_id(role_id, conn=db_conn)
    assert added_role is not None
    assert added_role["role_name"] == role_name
    assert added_role["description"] is None

# Pour exécuter ces tests:
# 1. Assurez-vous que pytest est installé (`pip install pytest`)
# 2. Naviguez vers la racine du projet
# 3. Exécutez `pytest tests/db/cruds/test_roles_crud.py` ou `pytest` pour tous les tests.
#
# Note: La fixture db_conn recrée la table Roles pour chaque test.
# Pour des suites de tests plus grandes, on pourrait vouloir initialiser le schéma une fois par session.
# La fonction initialize_database de db.init_schema pourrait être adaptée pour prendre un objet de connexion
# et être utilisée dans la fixture pour un setup de schéma plus complet si d'autres tables sont nécessaires.
# Le `@_manage_conn` décorateur dans roles_crud.py gère commit/rollback, donc les tests n'ont pas besoin de le faire.
#
# Si roles_crud.py utilisait une instance de GenericCRUD, les tests seraient similaires mais appelleraient
# des méthodes sur cette instance (par exemple, `roles_crud_instance.add_role(...)`).
# Puisque roles_crud.py a des fonctions au niveau du module, on les appelle directement.
