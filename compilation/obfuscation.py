"""
This script defines the obfuscation process for the application.

Obfuscation is the process of making the source code difficult to understand,
which helps to protect the intellectual property of the application.

This script will use pyarmor to obfuscate the python source code.
"""

import os
import shutil
import subprocess

# --- Configuration ---
# The directory containing the source code to be obfuscated.
SRC_DIR = "src"
# The directory where the obfuscated code will be stored.
OBFUSCATED_DIR = "dist/obfuscated_src"
# The entry point of the application.
ENTRY_POINT = "main.py"

def clean_up():
    """
    Cleans up temporary files and directories created during the obfuscation process.
    """
    print("Cleaning up temporary files...")
    if os.path.exists(OBFUSCATED_DIR):
        shutil.rmtree(OBFUSCATED_DIR)
    print("Clean up complete.")

def obfuscate_files():
    """
    Obfuscates the python files in the project using pyarmor.
    """
    print("Obfuscating files...")
    try:
        # The command to obfuscate the code.
        command = [
            "pyarmor",
            "obfuscate",
            "--recursive",
            "--output",
            OBFUSCATED_DIR,
            os.path.join(SRC_DIR, ENTRY_POINT)
        ]
        # Execute the command.
        subprocess.run(command, check=True)
        print("Files obfuscated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during obfuscation: {e}")
    except FileNotFoundError:
        print("Error: pyarmor is not installed or not in the system's PATH.")
        print("Please install it using: pip install pyarmor")

if __name__ == "__main__":
    # Clean up previous obfuscated files before running the process.
    clean_up()
    # Obfuscate the files.
    obfuscate_files()
