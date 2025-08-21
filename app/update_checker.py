import logging
import requests
import json
import os
import subprocess

from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication
from packaging.version import parse as parse_version

from ._version import __version__
from app.views.gui.dialogs.update_dialog import UpdateDialog
from app.views.gui.dialogs.download_progress_dialog import DownloadProgressDialog

# This should point to the location of your version manifest file on a server.
VERSION_INFO_URL = "https://raw.githubusercontent.com/leopardo-ai/main/version.json" # Example URL

class UpdateChecker:
    def __init__(self, parent=None):
        self.parent = parent
        self.update_info = {}

    def check_for_updates(self, silent=True):
        """
        Checks for updates and shows a dialog if a new version is available.
        :param silent: If True, only shows a dialog if an update is found.
                       If False, shows a message even if no update is found.
        """
        logging.info(f"Checking for updates from {VERSION_INFO_URL}...")
        try:
            response = requests.get(VERSION_INFO_URL, timeout=10)
            response.raise_for_status()
            self.update_info = response.json()

            local_version = parse_version(__version__)
            remote_version = parse_version(self.update_info.get("version"))

            logging.info(f"Local version: {local_version}, Remote version: {remote_version}")

            if remote_version > local_version:
                self.show_update_dialog()
            elif not silent:
                self.show_no_update_dialog()

        except requests.RequestException as e:
            logging.error(f"Failed to fetch update information: {e}")
            if not silent:
                self.show_error_dialog(f"Could not connect to the update server: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Failed to parse version information: {e}")
            if not silent:
                self.show_error_dialog("The update information file appears to be corrupt.")

    def show_update_dialog(self):
        """
        Displays a custom dialog box to the user with update information.
        """
        if self.parent is None:
            logging.error("Cannot show update dialog without a parent window.")
            return

        version = self.update_info.get("version", "N/A")
        notes = self.update_info.get("notes", "No release notes provided.")

        dialog = UpdateDialog(version, notes, self.parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            logging.info("User chose to update.")
            self.download_update()
        else:
            logging.info("User chose not to update.")

    def show_no_update_dialog(self):
        """Informs the user they are up to date."""
        QMessageBox.information(self.parent, "No Updates", "You are using the latest version of the application.")

    def show_error_dialog(self, message):
        """Shows a generic error dialog."""
        QMessageBox.warning(self.parent, "Update Check Failed", message)

    def download_update(self):
        """
        Initiates the download of the new installer using a progress dialog.
        """
        download_url = self.update_info.get("url")
        if not download_url:
            logging.error("No download URL found in version information.")
            self.show_error_dialog("Could not find the download link for the new version.")
            return

        logging.info(f"Starting download from: {download_url}")

        dialog = DownloadProgressDialog(download_url, self.parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            save_path = dialog.save_path
            logging.info(f"Download finished. Launching installer at {save_path}")
            try:
                if os.name == 'nt':
                    os.startfile(save_path)
                else:
                    subprocess.run(['chmod', '+x', save_path], check=True)
                    subprocess.Popen([save_path])

                QApplication.instance().quit()

            except Exception as e:
                logging.error(f"Failed to launch installer: {e}")
                self.show_error_dialog(f"Could not start the installer.\nPlease find it at: {save_path}")
