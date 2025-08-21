import os
import requests
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class DownloadThread(QThread):
    """
    Worker thread to download the file in the background.
    """
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.is_running = True

    def run(self):
        try:
            with requests.get(self.url, stream=True, timeout=15) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                bytes_downloaded = 0

                with open(self.save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not self.is_running:
                            self.error.emit("Download cancelled.")
                            return
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            progress_percent = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(progress_percent)

            if self.is_running:
                self.finished.emit(self.save_path)

        except requests.RequestException as e:
            self.error.emit(f"Network error: {e}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")

    def stop(self):
        self.is_running = False

class DownloadProgressDialog(QDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads", os.path.basename(self.url))

        self.setWindowTitle("Downloading Update")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        self.label = QLabel("Downloading new version...")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Cancel")
        self.launch_button = QPushButton("Launch Installer")
        self.launch_button.setVisible(False)

        layout.addWidget(self.cancel_button)
        layout.addWidget(self.launch_button)

        self.download_thread = DownloadThread(self.url, self.save_path)

        self.cancel_button.clicked.connect(self.cancel_download)
        self.launch_button.clicked.connect(self.launch_installer)

        self.download_thread.progress.connect(self.set_progress)
        self.download_thread.finished.connect(self.on_finished)
        self.download_thread.error.connect(self.on_error)

        self.download_thread.start()

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def on_finished(self, save_path):
        self.label.setText("Download complete!")
        self.progress_bar.setValue(100)
        self.cancel_button.setVisible(False)
        self.launch_button.setVisible(True)
        QMessageBox.information(self, "Success", f"Installer downloaded to:\n{save_path}")

    def on_error(self, message):
        QMessageBox.warning(self, "Download Failed", message)
        self.close()

    def cancel_download(self):
        self.download_thread.stop()
        self.close()

    def launch_installer(self):
        # This will be implemented in the main update_checker module
        # to handle quitting the application properly.
        self.accept()

    def closeEvent(self, event):
        self.cancel_download()
        event.accept()
