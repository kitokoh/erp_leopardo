# run_import_smoketest.py
import sys
import os
import importlib

# Ensure the project root is in sys.path for consistent imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
elif sys.path[0] != PROJECT_ROOT:
    sys.path.remove(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

print(f"--- Import Smoke Test Initializing ---")
print(f"PROJECT_ROOT set to: {PROJECT_ROOT}")
print(f"sys.path[0] is: {sys.path[0]}")
print(f"--- Starting Imports ---")

# List of modules to test importing
# This list should be maintained and updated as the project evolves.
# Reduced list for testing timeout issue
modules_to_test = [
    "main",
    "app_setup",
    "config",
    "db",
    "gui.main_window", # This one pulls in a lot, will be a good test
    "utils.app_constants",
    "auth.authentication",
    "services.email_service",
    "license_management"
]

failed_imports = 0
successful_imports = 0

for module_name in modules_to_test:
    try:
        importlib.import_module(module_name)
        print(f"[SUCCESS] Successfully imported '{module_name}'")
        successful_imports += 1
    except ImportError as e:
        print(f"[FAILURE] Failed to import '{module_name}': {e}")
        failed_imports += 1
    except Exception as e: # Catch other potential errors during import (like syntax errors)
        print(f"[ERROR] An unexpected error occurred while importing '{module_name}': {e}")
        failed_imports += 1

print(f"\n--- Import Smoke Test Summary ---")
print(f"Successfully imported: {successful_imports} module(s)")
print(f"Failed to import:    {failed_imports} module(s)")

if failed_imports > 0:
    print("\n[RESULT] Smoke test FAILED due to import errors.")
    sys.exit(1)
else:
    print("\n[RESULT] Smoke test PASSED. All key modules imported successfully.")
    sys.exit(0)
