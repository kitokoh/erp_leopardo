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
    print("Installation of Invoice Ninja is currently disabled.")
    return

def install_next_erp():
    print("Installation of NextERP is currently disabled.")
    return

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
        return os.path.exists("invoiceninja/artisan")
    elif app_id == "next-erp":
        return os.path.exists("bench/bench")
    return False

def rename_app(app_id, new_name):
    original_name = ""
    app_path = ""
    if app_id == "n8n":
        original_name = "n8n"
        # n8n is a global npm package, so we can't easily rename it.
        # We will focus on the other two for now.
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

def install_and_launch_app(app_id):
    if app_id == "invoice-ninja" or app_id == "next-erp":
        print(f"Installation of {app_id} is currently disabled.")
        return None

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
            print(f"Launching {app_id}...")
            try:
                subprocess.Popen(launch_command)
                return url
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Error launching {app_id}: {e}")
                return None
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
