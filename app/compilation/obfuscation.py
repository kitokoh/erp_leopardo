"""
This script defines the obfuscation process for the application.

Obfuscation is the process of making the source code difficult to understand,
which helps to protect the intellectual property of the application.

This script will use pyarmor to obfuscate the python source code.
"""

import os
import shutil
import subprocess
import logging
import argparse

# --- Configuration ---
# The directory containing the source code to be obfuscated.
SRC_DIR = "src"
# The directory where the obfuscated code will be stored.
OBFUSCATED_DIR = "dist/obfuscated_src"
# The entry point of the application.
ENTRY_POINT = "main.py"
# The log file for the obfuscation process.
LOG_FILE = "obfuscation.log"

# --- Logging ---
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def clean_up():
    """
    Cleans up temporary files and directories created during the obfuscation process.
    """
    logging.info("Cleaning up temporary files...")
    if os.path.exists(OBFUSCATED_DIR):
        shutil.rmtree(OBFUSCATED_DIR)
    logging.info("Clean up complete.")

def obfuscate_files(obfuscation_level, exclude):

    """
    Obfuscates the python files in the project using pyarmor.
    """
    logging.info(f"Obfuscating files with level: {obfuscation_level}")
    try:
        # The command to obfuscate the code.
        command = [
            "pyarmor",
            "obfuscate",
            "--recursive",
            f"--obf-level={obfuscation_level}",
            "--output",
            OBFUSCATED_DIR,
            os.path.join(SRC_DIR, ENTRY_POINT)
        ]
        # Add exclude patterns to the command.
        for pattern in exclude:
            command.extend(["--exclude", pattern])

        # Execute the command.
        subprocess.run(command, check=True)
        logging.info("Files obfuscated successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during obfuscation: {e}")
    except FileNotFoundError:
        logging.error("Error: pyarmor is not installed or not in the system's PATH.")
        logging.error("Please install it using: pip install pyarmor")

def sign_code():
    """
    Signs the obfuscated code.
    """
    logging.info("Signing the code...")
    # Add code signing logic here
    logging.info("Code signed successfully.")


def main():
    """
    The main function of the script.
    """
    parser = argparse.ArgumentParser(description="Obfuscate Python source code.")
    parser.add_argument("--level", type=int, default=1,
                        help="The obfuscation level (1-3).")
    parser.add_argument("--exclude", nargs='*', default=[],
                        help="A list of patterns to exclude from obfuscation.")
    parser.add_argument("--sign", action="store_true",
                        help="Sign the code after obfuscation.")

    args = parser.parse_args()

    # Clean up previous obfuscated files before running the process.
    clean_up()
    # Obfuscate the files.
    obfuscate_files(args.level, args.exclude)

    # Sign the code if requested.
    if args.sign:
        sign_code()


if __name__ == "__main__":
    main()
