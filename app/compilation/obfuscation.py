"""
This script defines the obfuscation process for the application.
It is designed to be called from the main build script.
"""

import os
import sys
import subprocess
import logging

# Adjust path to import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from build_config import OBFUSCATED_SRC_DIR, MAIN_SCRIPT, OBFUSCATION_LEVEL

def obfuscate_code(entry_script, output_dir, exclude=None):
    """
    Obfuscates the python files in the project using pyarmor.

    :param entry_script: The main entry point of the application.
    :param output_dir: The directory to store the obfuscated code.
    :param exclude: A list of patterns to exclude from obfuscation.
    """
    if exclude is None:
        exclude = []

    logging.info(f"Starting obfuscation for '{entry_script}'...")
    logging.info(f"Output directory: '{output_dir}'")
    logging.info("Using simplified obfuscation for debugging.")

    # The entry script path needs to be relative to the project root for PyArmor
    # The `entry_script` from config is 'app/main.py'.
    # We need to run pyarmor from the root of the project.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # The entry point for obfuscation should be the main script of the app
    obfuscation_entry = os.path.join(project_root, entry_script)

    try:
        command = [
            "pyarmor-7", "obfuscate",
            "--recursive",
            "--output", output_dir,
            obfuscation_entry
        ]

        for pattern in exclude:
            command.extend(["--exclude", pattern])

        # We need to run this command from the project root
        process = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        logging.info("PyArmor output:\n" + process.stdout)
        logging.info("Files obfuscated successfully.")
        return True

    except FileNotFoundError:
        logging.error("Error: pyarmor is not installed or not in the system's PATH.")
        logging.error("Please install it using: pip install pyarmor")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during obfuscation.")
        logging.error("PyArmor Stderr:\n" + e.stderr)
        logging.error("PyArmor Stdout:\n" + e.stdout)
        return False


def run():
    """
    Main function to run the obfuscation process.
    This is called from the main build.py script.
    """
    logging.info("--- Running Obfuscation Step ---")

    # Example of excluding files if needed in the future
    # exclude_patterns = ["some_module_to_exclude"]
    exclude_patterns = []

    if not obfuscate_code(MAIN_SCRIPT, OBFUSCATED_SRC_DIR, exclude_patterns):
        logging.error("Obfuscation failed. Aborting build.")
        sys.exit(1)

    logging.info("--- Obfuscation Step Completed ---")


if __name__ == "__main__":
    # This allows running the script directly for testing purposes
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run()
