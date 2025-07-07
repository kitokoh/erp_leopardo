# Agent Notes and Development Guidelines

This document provides notes and guidelines for AI agents (and human developers) working on this project.

## Import Smoke Test

A basic import smoke test script, `run_import_smoketest.py`, is available in the project root.

**Purpose:**
This script attempts to import a curated list of key application modules to quickly check for:
- `ModuleNotFoundError`s due to incorrect paths or missing files.
- Basic `ImportError`s that might arise from syntax errors within modules or immediate circular dependencies detectable at import time.

**How to Run:**
From the project root directory, execute:
```bash
python run_import_smoketest.py
```

**Expected Output:**
The script will print `[SUCCESS]` or `[FAILURE]` for each module it attempts to import.
At the end, it will provide a summary and exit with status code 0 if all tested imports succeed, or 1 if any fail.

**Limitations in Certain Environments:**
In some restricted or performance-constrained environments (like certain sandboxes), this script might time out if it attempts to import a very large number of modules or if specific modules (especially those with heavy C extensions or GUI dependencies like PyQt5) hang during initialization. If a timeout occurs, try reducing the list of modules in `modules_to_test` within the script to pinpoint problematic imports or to test a core subset.

**Maintenance:**
The `modules_to_test` list in `run_import_smoketest.py` should be periodically reviewed and updated as the project evolves to include new critical modules or to reflect changes in project structure.

## Coding Conventions (Example - To Be Expanded)

- Follow PEP 8 guidelines for Python code.
- Use absolute imports where possible, relative imports for intra-package modules.
- Ensure all new modules have appropriate logging (`logger = logging.getLogger(__name__)`).

## Running the Main Application

- Due to GUI components, the main application (`main.py`) may require a virtual display environment like Xvfb if run in a headless server environment:
  ```bash
  xvfb-run python main.py
  ```

## Known Issues / Areas for Attention (as of last agent interaction)

- **`db.cruds.media_items_crud` Warning:** A persistent warning `WARNING:root:db.cruds.media_items_crud module not found` occurs at startup. The file exists, and the import mechanism in `db/cruds/__init__.py` has a try-except block that handles this by providing stubs. The exact cause of the initial `ImportError` for this specific module is still elusive but does not prevent application startup.
- **`html_to_pdf_util` Error:** An error `ERROR:root:Failed to import html_to_pdf_util` may indicate missing system dependencies for WeasyPrint (e.g., Pango, Cairo, GDK-PixBuf) or issues within the utility itself. While the import path has been corrected, full functionality isn't confirmed.
- **`local_voice_handler` Warning:** A warning `WARNING:security_module.biometric_auth:Local voice handler module not found or import error` occurs because optional dependencies (sounddevice, librosa, etc.) are not installed. This is handled gracefully by the application.
- **`objc` Import Error in Windows Biometric Handler:** An error `ERROR:security_module.biometric_auth:Failed to import Windows biometric handler: No module named 'objc'` was noted. This is unexpected for a Windows handler and needs investigation.
- **Missing SVG Icons:** Some `qt.svg: Cannot open file ...` errors indicate missing icon resources. These should be added to the QRC file or project resources.

(Further sections can be added as needed)
