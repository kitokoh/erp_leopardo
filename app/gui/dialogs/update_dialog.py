from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextBrowser, QPushButton, QHBoxLayout,
    QApplication
)
from PyQt5.QtCore import Qt

class UpdateDialog(QDialog):
    def __init__(self, version, notes, parent=None):
        super().__init__(parent)
        self.version = version
        self.notes = notes
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        title_label = QLabel(f"A new version ({self.version}) is available!")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        intro_label = QLabel("We recommend that you update to the latest version.")
        layout.addWidget(intro_label)

        notes_label = QLabel("Release Notes:")
        notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(notes_label)

        notes_browser = QTextBrowser()
        notes_browser.setPlainText(self.notes)
        notes_browser.setOpenExternalLinks(True) # In case notes contain links
        layout.addWidget(notes_browser)

        # Button layout
        button_layout = QHBoxLayout()

        self.remind_button = QPushButton("Remind Me Later")
        self.remind_button.clicked.connect(self.reject) # Closes dialog, returns QDialog.Rejected
        button_layout.addWidget(self.remind_button)

        self.install_button = QPushButton("Install Now")
        self.install_button.setDefault(True)
        self.install_button.clicked.connect(self.accept) # Closes dialog, returns QDialog.Accepted
        button_layout.addWidget(self.install_button)

        layout.addLayout(button_layout)

if __name__ == '__main__':
    # Example of how to run the dialog for testing
    import sys
    app = QApplication(sys.argv)

    # Example data
    example_version = "2.1.0"
    example_notes = "- New feature X\n- Bug fix Y\n- Performance improvements"

    dialog = UpdateDialog(example_version, example_notes)

    # To see the result of the user's choice
    if dialog.exec_() == QDialog.Accepted:
        print("User chose to install.")
    else:
        print("User chose to be reminded later.")

    sys.exit(app.exec_())
