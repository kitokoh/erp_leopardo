# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import platform
import fileinput

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
    subprocess.run([commands["install"], "git", "php", "composer"])

    # Clone the repo
    subprocess.run(["git", "clone", "https://github.com/invoiceninja/invoiceninja.git"])

    # Install PHP dependencies
    os.chdir("invoiceninja")
    subprocess.run([commands["php_deps"][0], commands["php_deps"][1], "install"])
    os.chdir("..")

def install_next_erp():
    commands = get_os_commands()
    if not commands:
        print("Unsupported OS")
        return

    # Install dependencies
    subprocess.run([commands["install"], "git", "python3", "python3-pip"])

    # Clone the repo
    subprocess.run(["git", "clone", "https://github.com/frappe/bench.git"])

    # Install bench
    os.chdir("bench")
    subprocess.run([commands["python_deps"], "install", "--editable", "."])

    # Create a new site
    subprocess.run(["bench", "new-site", "leopardo-web-erp.com"])

    # Install erpnext
    subprocess.run(["bench", "get-app", "erpnext"])
    subprocess.run(["bench", "install-app", "erpnext"])

    os.chdir("..")

def get_installer_command(app_id):
    if app_id == "n8n":
        return install_n8n
    elif app_id == "invoice-ninja":
        return install_invoice_ninja
    elif app_id == "next-erp":
        return install_next_erp
    return None

def get_launch_command(app_id):
    if app_id == "n8n":
        return ["n8n"]
    elif app_id == "invoice-ninja":
        # This is not the real launch command.
        return ["php", "invoiceninja/artisan", "serve"]
    elif app_id == "next-erp":
        os.chdir("bench")
        return ["bench", "start"]
    return None

def is_installed(app_id):
    if app_id == "n8n":
        return subprocess.run(["which", "n8n"], capture_output=True).returncode == 0
    elif app_id == "invoice-ninja":
        return os.path.exists("invoiceninja")
    elif app_id == "next-erp":
        return os.path.exists("bench")
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

def install_and_launch_app(app_id):
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
            installer()
            rename_app(app_id, new_name)
        else:
            print(f"Installer for {app_id} not found.")
            return

    launch_command = get_launch_command(app_id)
    if launch_command:
        print(f"Launching {app_id}...")
        subprocess.run(launch_command)
    else:
        print(f"Launch command for {app_id} not found.")
