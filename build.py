import os
import sys
import shutil
import subprocess
import logging
import argparse
import importlib.util
from build_config import *

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("build.log", mode='w'),
        logging.StreamHandler()
    ]
)

def run_command(command, cwd="."):
    """Runs a command and logs its output."""
    logging.info(f"Running command: {' '.join(command)}")
    try:
        process = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        logging.info("Command output:\n" + process.stdout)
        if process.stderr:
            logging.warning("Command stderr:\n" + process.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}")
        logging.error("Stderr:\n" + e.stderr)
        logging.error("Stdout:\n" + e.stdout)
        return False

def inject_version_info():
    """Writes the app version to a file that the application can access."""
    logging.info(f"Injecting version '{APP_VERSION}' into app/_version.py")
    version_file_path = os.path.join('app', '_version.py')
    with open(version_file_path, 'w') as f:
        f.write(f'__version__ = "{APP_VERSION}"\n')
    logging.info("Version injection complete.")
    return True

def clean():
    """Remove previous build and distribution artifacts."""
    logging.info("--- Cleaning up previous build artifacts ---")
    for path in [BUILD_DIR, DIST_DIR, OBFUSCATED_SRC_DIR]:
        if os.path.exists(path):
            shutil.rmtree(path)
            logging.info(f"Removed directory: {path}")
    if os.path.exists("build.log"):
        os.remove("build.log")
    # Also remove the generated version file
    if os.path.exists(os.path.join('app', '_version.py')):
        os.remove(os.path.join('app', '_version.py'))
        logging.info("Removed app/_version.py")

    os.makedirs(OBFUSCATED_SRC_DIR, exist_ok=True)
    os.makedirs(INSTALLER_DIR, exist_ok=True)
    logging.info("--- Cleanup complete ---")

def run_obfuscation():
    """Run the code obfuscation script."""
    logging.info("--- Starting Obfuscation Step ---")
    try:
        spec = importlib.util.spec_from_file_location("obfuscation_runner", OBFUSCATION_SCRIPT)
        obfuscation_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(obfuscation_module)
        obfuscation_module.run()
        logging.info("--- Obfuscation Step Finished ---")
        return True
    except Exception as e:
        logging.error(f"Failed to run obfuscation script: {e}", exc_info=True)
        return False

def generate_spec_from_template(use_obfuscation=True):
    """Generates the final spec file from the template."""
    logging.info(f"Generating spec file (use_obfuscation={use_obfuscation})...")
    spec_template_path = f"{SPEC_FILE}.tpl"

    with open(spec_template_path, 'r') as f:
        template_content = f.read()

    # Use absolute paths to avoid issues with PyInstaller's working directory.
    project_root = os.path.abspath(os.getcwd())
    app_dir = os.path.join(project_root, 'app')

    if use_obfuscation:
        # This part is still broken, we'll focus on the non-obfuscated path
        logging.info("Using OBFUSCATED source for spec file.")
        entry_script = os.path.join(project_root, OBFUSCATED_SRC_DIR, 'app', MAIN_SCRIPT)
        source_path = os.path.join(project_root, OBFUSCATED_SRC_DIR)
    else:
        logging.info("Using ORIGINAL source for spec file.")
        entry_script = os.path.join(app_dir, MAIN_SCRIPT)
        source_path = project_root

    # Corrected paths to resources
    resources_path = os.path.join(app_dir, 'resources')
    seed_data_path = os.path.join(app_dir, 'db', 'seed_data')
    app_icon_path = os.path.join(project_root, APP_ICON)
    dist_dir_path = os.path.join(project_root, DIST_DIR)
    build_dir_path = os.path.join(project_root, BUILD_DIR)

    replacements = {
        "__entry_script__": entry_script.replace('\\', '/'),
        "__source_path__": source_path.replace('\\', '/'),
        "__project_root__": project_root.replace('\\', '/'),
        "__resources_path__": resources_path.replace('\\', '/'),
        "__seed_data_path__": seed_data_path.replace('\\', '/'),
        "__app_dir__": app_dir.replace('\\', '/'),
        "__app_name__": APP_NAME,
        "__app_icon__": app_icon_path.replace('\\', '/'),
        "__dist_dir__": dist_dir_path.replace('\\', '/'),
        "__build_dir__": build_dir_path.replace('\\', '/')
    }

    content = template_content
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    with open(SPEC_FILE, 'w') as f:
        f.write(content)

    logging.info(f"Successfully generated '{SPEC_FILE}'")
    return True


def run_pyinstaller(use_obfuscation=True):
    """Run PyInstaller to create the executable."""
    logging.info("--- Starting PyInstaller Step ---")
    if not generate_spec_from_template(use_obfuscation):
        logging.error("Failed to generate spec file. Aborting.")
        return False

    command = ["pyinstaller", "--noconfirm", SPEC_FILE]
    if run_command(command):
        logging.info("--- PyInstaller Step Finished ---")
        return True
    else:
        logging.error("PyInstaller step failed.")
        return False

def run_inno_setup():
    """Run Inno Setup to create the installer."""
    logging.info("--- Starting Inno Setup Step ---")
    # Path to Inno Setup compiler. Assumes it's in PATH.
    # On a typical Windows system, it might be:
    # 'C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe'
    iscc_executable = "iscc"

    defines = [
        f"/DMyAppName=\"{APP_NAME}\"",
        f"/DMyAppVersion=\"{APP_VERSION}\"",
        f"/DMyAppPublisher=\"{COMPANY_NAME}\"",
        f"/DMyAppExeName=\"{APP_NAME}.exe\"",
        f"/DSourceDir=\"{DIST_DIR}\"",
        f"/DInstallerOutputDir=\"{INSTALLER_DIR}\"",
        f"/DAppIcon=\"{APP_ICON}\""
    ]

    command = [iscc_executable] + defines + [ISS_FILE]

    if run_command(command):
        logging.info("--- Inno Setup Step Finished ---")
        return True
    else:
        logging.error("Inno Setup step failed.")
        return False

def main():
    """Main build process orchestrator."""
    parser = argparse.ArgumentParser(description=f"Build script for {APP_NAME}")
    parser.add_argument(
        "command",
        choices=["build", "clean", "obfuscate", "package", "full"],
        help="The build command to execute."
    )
    parser.add_argument(
        "--no-obfuscation",
        action="store_true",
        help="Skip the obfuscation step during a full build."
    )
    args = parser.parse_args()

    if args.command == "clean":
        clean()
    elif args.command == "obfuscate":
        if not run_obfuscation(): sys.exit(1)
    elif args.command == "build":
        # Pass the obfuscation flag to pyinstaller
        if not run_pyinstaller(use_obfuscation=not args.no_obfuscation): sys.exit(1)
    elif args.command == "package":
        if not run_inno_setup(): sys.exit(1)
    elif args.command == "full":
        clean()
        if not inject_version_info():
            sys.exit(1)

        use_obfuscation = not args.no_obfuscation
        if use_obfuscation:
            if not run_obfuscation():
                logging.warning("Obfuscation failed. Continuing build without it.")
                use_obfuscation = False

        if not run_pyinstaller(use_obfuscation=use_obfuscation):
            sys.exit(1)

        if not run_inno_setup():
            sys.exit(1)

        logging.info("--- Full build process completed successfully! ---")
        logging.info(f"Installer created at: {os.path.join(INSTALLER_DIR)}")

if __name__ == "__main__":
    main()
