# run_import_smoketest.py
import sys
import os
import importlib
import logging
from pathlib import Path

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Project Path Setup ---
try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    logging.info(f"--- Import Smoke Test Initializing ---")
    logging.info(f"PROJECT_ROOT set to: {PROJECT_ROOT}")
    logging.info(f"sys.path[0] is now: {sys.path[0]}")
except Exception as e:
    logging.critical(f"Failed to set up PROJECT_ROOT and sys.path: {e}")
    sys.exit(1)

def find_python_modules(root_dir: Path):
    """Finds all .py files and converts them to module import strings."""
    modules = []
    for path in root_dir.rglob('*.py'):
        if path.name == '__init__.py':
            continue  # Skip __init__.py files for direct import test

        # Create module string relative to the project root
        relative_path = path.relative_to(PROJECT_ROOT)
        module_string = str(relative_path).replace(os.path.sep, '.').replace('.py', '')

        # Exclude certain problematic or non-essential files/folders
        if any(part in module_string for part in ['migrations.versions', 'tests', 'venv', '.venv']):
            continue

        modules.append(module_string)
    return modules

def run_test():
    """
    Iterates through all found Python modules and attempts to import each one.
    Reports success or failure for each module.
    """
    app_dir = PROJECT_ROOT / 'app'
    modules_to_test = find_python_modules(app_dir)

    logging.info(f"\n--- Starting Import Test for {len(modules_to_test)} modules ---")

    successful_imports = []
    failed_imports = []

    for module_path in modules_to_test:
        try:
            print(f"Attempting to import: {module_path}") # More direct print
            logging.info(f"Attempting to import: {module_path}")
            importlib.import_module(module_path)
            # logging.info(f"[SUCCESS] Imported: {module_path}")
            successful_imports.append(module_path)
        except ImportError as e:
            logging.error(f"[FAILURE] Failed to import '{module_path}'. Error: {e}")
            failed_imports.append((module_path, str(e)))
        except Exception as e:
            logging.error(f"[ERROR] An unexpected error occurred while importing '{module_path}': {e}")
            failed_imports.append((module_path, str(e)))

    # --- Summary ---
    logging.info("\n--- Import Smoke Test Summary ---")
    logging.info(f"Successfully imported: {len(successful_imports)} module(s)")
    logging.info(f"Failed to import:    {len(failed_imports)} module(s)")

    if failed_imports:
        logging.error("\n[RESULT] Smoke test FAILED. The following modules could not be imported:")
        for module, error in failed_imports:
            logging.error(f"  - {module}: {error}")
        sys.exit(1)
    else:
        logging.info("\n[RESULT] Smoke test PASSED. All key modules imported successfully.")
        sys.exit(0)

if __name__ == "__main__":
    run_test()
