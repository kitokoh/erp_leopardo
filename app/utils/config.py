# utils/config.py
import os
import json
import secrets
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
    config_needs_saving = False

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}. Reverting to defaults.")
            user_config = {} # Start fresh if config is corrupt
    else:
        user_config = {}

    # Define defaults
    default_config = {
        "templates_dir": default_templates_dir,
        "clients_dir": default_clients_dir,
        "database_path": os.path.join(app_root_dir, "app_data.db"),
        "database_type": "sqlite",
        "language": "fr",
        "smtp_server": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "default_reminder_days": 30,
        "download_monitor_enabled": False,
        "download_monitor_path": os.path.join(os.path.expanduser('~'), 'Downloads'),
        "API_SECRET_KEY": secrets.token_hex(32) # Always generate a secure default
    }

    # Merge defaults into user_config for any missing keys
    for key, value in default_config.items():
        if key not in user_config:
            user_config[key] = value
            config_needs_saving = True
            print(f"Config key '{key}' was missing. Set to default.")

    # Specifically check for API_SECRET_KEY and regenerate if empty or weak, for security.
    if not user_config.get("API_SECRET_KEY") or len(user_config.get("API_SECRET_KEY", "")) < 64:
        user_config["API_SECRET_KEY"] = secrets.token_hex(32)
        config_needs_saving = True
        print("API_SECRET_KEY was missing, empty, or weak. A new secure key has been generated.")

    if config_needs_saving:
        print("Configuration updated with defaults or new keys, saving...")
        save_config(user_config)

    return user_config

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
