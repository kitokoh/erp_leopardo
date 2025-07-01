# utils/config.py
import os
import json
from PyQt5.QtCore import QStandardPaths, QCoreApplication
from PyQt5.QtWidgets import QMessageBox

# --- Configuration Constants ---
CONFIG_DIR_NAME = "ClientDocumentManager" # Consider if this should be globally configurable
CONFIG_FILE_NAME = "config.json"

# --- Configuration Functions ---
def get_config_dir():
    config_dir_path = os.path.join(
        QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation),
        CONFIG_DIR_NAME
    )
    os.makedirs(config_dir_path, exist_ok=True)
    return config_dir_path

def get_config_file_path():
    return os.path.join(get_config_dir(), CONFIG_FILE_NAME)

def load_config(app_root_dir, default_templates_dir, default_clients_dir):
    """
    Loads configuration from JSON file.
    Requires app_root_dir to construct default paths if config file doesn't exist.
    """
    config_path = get_config_file_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Ensure 'database_type' defaults to 'sqlite' if not present
                user_config.setdefault('database_type', 'sqlite')
                return user_config
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}. Using defaults.")

    # If config file doesn't exist or is invalid, return defaults
    default_config = {
        "templates_dir": default_templates_dir, # Use passed default
        "clients_dir": default_clients_dir,     # Use passed default
        "database_path": os.path.join(app_root_dir, "app_data.db"),
        "database_type": "sqlite", # Ensure default is sqlite
        "language": "fr",
        "smtp_server": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "default_reminder_days": 30,
        "download_monitor_enabled": False,
        "download_monitor_path": os.path.join(os.path.expanduser('~'), 'Downloads')
    }
    return default_config

def save_config(config_data):
    try:
        config_path = get_config_file_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        QMessageBox.warning(None, QCoreApplication.translate("utils.save_config", "Erreur de Configuration"),
                            QCoreApplication.translate("utils.save_config", "Impossible d'enregistrer la configuration: {0}").format(e))

def is_first_launch(app_root_dir, default_templates_dir, default_clients_dir):
    """Checks if this is the first launch of the application."""
    config = load_config(app_root_dir, default_templates_dir, default_clients_dir)
    return not config.get("initial_setup_complete", False)

def mark_initial_setup_complete(app_root_dir, default_templates_dir, default_clients_dir):
    """Marks that the initial setup has been completed."""
    config = load_config(app_root_dir, default_templates_dir, default_clients_dir)
    config["initial_setup_complete"] = True
    save_config(config)
