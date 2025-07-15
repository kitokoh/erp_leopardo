# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import platform
import fileinput
import shutil

def get_os_commands():
    os_type = platform.system()
    if os_type == "Linux":
        return {
            "update": ["sudo", "apt-get", "update"],
            "install": ["sudo", "apt-get", "install", "-y"],
            "npm": ["sudo", "npm"],
            "php_deps": ["php", "composer"],
            "python_deps": ["pip"]
        }
    elif os_type == "Darwin": # macOS
        return {
            "update": ["brew", "update"],
            "install": ["brew", "install"],
            "npm": ["npm"],
            "php_deps": ["php", "composer"],
            "python_deps": ["pip"]
        }
    elif os_type == "Windows":
        return {
            "update": ["choco", "outdated"],
            "install": ["choco", "install"],
            "npm": ["npm.cmd"],
            "php_deps": ["php.exe", "composer.phar"],
            "python_deps": ["pip.exe"]
        }
    return None

def install_n8n():
    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return

    subprocess.run([commands["npm"], "install", "-g", "n8n"])

def install_invoice_ninja():
    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return

    # Install dependencies
    subprocess.run(commands["install"] + ["git", "php", "composer"])

    # Clone the repo
    if not os.path.exists("installed_addons/invoice-ninja"):
        os.makedirs("installed_addons/invoice-ninja")
    if not os.listdir("installed_addons/invoice-ninja"):
        subprocess.run(["git", "clone", "https://github.com/invoiceninja/invoiceninja.git", "installed_addons/invoice-ninja"])

    # Install PHP dependencies
    os.chdir("installed_addons/invoice-ninja")
    subprocess.run([commands["php_deps"][0], commands["php_deps"][1], "install"])
    os.chdir("../..")

def install_next_erp():
    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return

    # Install dependencies
    subprocess.run(commands["install"] + ["git", "python3", "python3-pip"])

    # Clone the repo
    if not os.path.exists("installed_addons/bench"):
        os.makedirs("installed_addons/bench")
    if not os.listdir("installed_addons/bench"):
        subprocess.run(["git", "clone", "https://github.com/frappe/bench.git", "installed_addons/bench"])

    # Install bench
    os.chdir("installed_addons/bench")
    subprocess.run([commands["python_deps"], "install", "--editable", "."])

    # Create a new site
    subprocess.run(["bench", "new-site", "leopardo-web-erp.com"])

    # Install erpnext
    subprocess.run(["bench", "get-app", "erpnext"])
    subprocess.run(["bench", "install-app", "erpnext"])

    os.chdir("../..")

def get_installer_command(app_id):
    if app_id == "n8n":
        return install_n8n
    elif app_id == "invoice-ninja":
        return install_invoice_ninja
    elif app_id == "next-erp":
        return install_next_erp
    return None

import webbrowser
from PyQt5.QtCore import QUrl

def get_launch_command(app_id):
    config = get_config(app_id)
    if app_id == "n8n":
        port = config.get("port", "5678")
        return ["n8n", "start", f"--port={port}"], QUrl(f"http://localhost:{port}")
    elif app_id == "invoice-ninja":
        return ["php", "invoiceninja/artisan", "serve"], QUrl("http://localhost:8000")
    elif app_id == "next-erp":
        os.chdir("bench")
        return ["bench", "start"], QUrl("http://localhost:8000")
    return None, None

def is_installed(app_id):
    if app_id == "n8n":
        return shutil.which("n8n") is not None
    elif app_id == "invoice-ninja":
        return os.path.exists("installed_addons/invoice-ninja/artisan")
    elif app_id == "next-erp":
        return os.path.exists("installed_addons/bench/bench")
    return False

def rename_app(app_id, new_name):
    original_name = ""
    app_path = ""
    if app_id == "n8n":
        config_path = os.path.expanduser("~/.n8n/config")
        with open(config_path, "a") as f:
            f.write("\nexport N8N_CUSTOM_ASSETS_DIR=$(pwd)/addons")
        return
    elif app_id == "invoice-ninja":
        original_name = "Invoice Ninja"
        app_path = "invoiceninja"
    elif app_id == "next-erp":
        original_name = "ERPNext"
        app_path = "bench/apps/erpnext"

    if not os.path.exists(app_path):
        print(f"Application path not found for {app_id}")
        return

    for dirpath, _, filenames in os.walk(app_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
                for line in file:
                    print(line.replace(original_name, new_name), end="")

def check_dependencies(app_id):
    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return False

    if app_id == "n8n":
        return shutil.which("npm") is not None
    elif app_id == "invoice-ninja":
        return shutil.which("git") is not None and shutil.which("php") is not None and shutil.which("composer") is not None
    elif app_id == "next-erp":
        return shutil.which("git") is not None and shutil.which("python3") is not None and shutil.which("pip") is not None
    return False

import importlib

from .context import AppContext

def launch_plugin(app_id, main_window):
    manifest_path = os.path.join("plugins", app_id, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Manifest for plugin {app_id} not found.")
        return

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    entry_point = manifest["entry_point"]
    module_name, function_name = entry_point.split(":")

    plugin_path = os.path.join("plugins", app_id)
    sys.path.insert(0, plugin_path)

    module = importlib.import_module(module_name)
    function = getattr(module, function_name)

    context = AppContext(main_window)
    function(context)

    sys.path.pop(0)

from .process_manager import process_manager

def install_and_launch_app(app_id, main_window):
    if os.path.exists(os.path.join("plugins", app_id)):
        launch_plugin(app_id, main_window)
        return QUrl("about:blank")

    if not check_dependencies(app_id):
        print(f"Dependencies for {app_id} are not installed. Please install them manually.")
        return None

    new_name = ""
    if app_id == "n8n":
        new_name = "Leopardo Agent"
    elif app_id == "invoice-ninja":
        new_name = "Leopardo Invoice"
    elif app_id == "next-erp":
        new_name = "Leopardo Web ERP"

    if not is_installed(app_id):
        installer = get_installer_command(app_id)
        if installer:
            print(f"Installing {app_id}...")
            try:
                installer()
                rename_app(app_id, new_name)
            except Exception as e:
                print(f"Error installing {app_id}: {e}")
                return None
        else:
            print(f"Installer for {app_id} not found.")
            return None

    if is_installed(app_id):
        launch_command, url = get_launch_command(app_id)
        if launch_command:
            process_manager.start(app_id, launch_command)
            return url
        else:
            print(f"Launch command for {app_id} not found.")
            return None

    return None

def uninstall_app(app_id):
    if not is_installed(app_id):
        return

    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return

    if app_id == "n8n":
        subprocess.run([commands["npm"], "uninstall", "-g", "n8n"])
    elif app_id == "invoice-ninja":
        shutil.rmtree("invoiceninja")
    elif app_id == "next-erp":
        shutil.rmtree("bench")

def get_config_path(app_id):
    return f"addons/{app_id}_config.json"

def get_config(app_id):
    path = get_config_path(app_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_config(app_id, config):
    path = get_config_path(app_id)
    with open(path, "w") as f:
        json.dump(config, f, indent=4)

def update_app(app_id):
    if not is_installed(app_id):
        return

    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return

    if app_id == "n8n":
        subprocess.run([commands["npm"], "install", "-g", "n8n@latest"])
    elif app_id == "invoice-ninja":
        os.chdir("invoiceninja")
        subprocess.run(["git", "pull"])
        os.chdir("..")
    elif app_id == "next-erp":
        os.chdir("bench")
        subprocess.run(["bench", "update"])
        os.chdir("..")
