import sys
import os
import subprocess

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"conftest.py: Injected project root '{project_root}' into sys.path.")

# --- Start of Environment Fix ---
# Find the poetry virtual environment and add its site-packages to the path.
# This ensures that tests can find the installed dependencies.
try:
    # Use `poetry env info -p` to get the venv path directly.
    result = subprocess.run(['poetry', 'env', 'info', '-p'], capture_output=True, text=True, check=True)
    venv_path = result.stdout.strip()

    # Construct the site-packages path. This might vary slightly based on OS/Python version.
    # A common structure is venv_path/lib/pythonX.Y/site-packages
    # We can list the contents of venv_path/lib to find the correct python version dir.
    # For now, we will assume a common structure.
    # Note: A more robust solution would be to parse `poetry run python -c "import sys; print(sys.path)"`
    # but that's more complex to implement here.

    # A simplified approach for now, assuming a standard layout.
    # This might need adjustment if the python version in the venv is different.
    py_version_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages_path = os.path.join(venv_path, 'lib', py_version_dir, 'site-packages')

    if os.path.exists(site_packages_path) and site_packages_path not in sys.path:
        sys.path.append(site_packages_path)
        print(f"conftest.py: Injected site-packages '{site_packages_path}' into sys.path.")
    else:
        if not os.path.exists(site_packages_path):
             print(f"conftest.py: WARNING - Constructed site-packages path does not exist: {site_packages_path}")
        # else:
        #      print(f"conftest.py: INFO - site-packages path already in sys.path: {site_packages_path}")

except (subprocess.CalledProcessError, FileNotFoundError):
    print("conftest.py: WARNING - Could not determine poetry venv path via `poetry env info -p`. Dependencies may not be found.")

print(f"conftest.py: Final sys.path: {sys.path}")
# --- End of Environment Fix ---
