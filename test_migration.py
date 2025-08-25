import os
import sys
import logging
import subprocess

# Ensure the app module is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG

def run_migration_test():
    """
    Tests only the database migration step.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # 1. Configure for a test-specific database
    CONFIG['database_path'] = os.path.join(project_root, 'test.db')
    CONFIG['database_url'] = f"sqlite:///{CONFIG['database_path']}"

    db_path = CONFIG['database_path']

    # 2. Delete the old test database
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info(f"Removed old test database: {db_path}")

    # 3. Run the Alembic migration
    logging.info("--- Running Alembic Migration ---")
    try:
        alembic_command = [sys.executable, "-m", "alembic", "upgrade", "head"]

        env = os.environ.copy()
        env['PYTHONPATH'] = project_root
        env['ALEMBIC_DATABASE_URL'] = CONFIG['database_url']

        result = subprocess.run(
            alembic_command,
            check=True, capture_output=True, text=True, cwd=project_root, env=env
        )
        logging.info("Alembic stdout:\n" + result.stdout)
        if result.stderr:
            logging.warning("Alembic stderr:\n" + result.stderr)

        if os.path.exists(db_path):
            logging.info(">>> Migration Test PASSED: Database file was created. <<<")
            return True
        else:
            logging.error(">>> Migration Test FAILED: Database file was not created. <<<")
            return False

    except subprocess.CalledProcessError as e:
        logging.error(">>> Migration Test FAILED: Alembic command failed.", exc_info=True)
        logging.error(f"Alembic Error:\n{e.stderr}")
        return False
    except Exception as e:
        logging.error(">>> Migration Test FAILED: An unexpected error occurred.", exc_info=True)
        return False

if __name__ == "__main__":
    if run_migration_test():
        sys.exit(0)
    else:
        sys.exit(1)
