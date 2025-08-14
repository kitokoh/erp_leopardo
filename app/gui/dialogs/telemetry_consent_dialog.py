from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

# We need the db_manager to save the setting
from app.db import db_manager

class TelemetryConsentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help Us Improve")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        title = QLabel("Help Improve Our Application")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        message_text = (
            "To help us improve the application, you can choose to send anonymous "
            "usage data to our team.\n\n"
            "This data helps us understand which features are most popular, "
            "identify problems, and guide future development. We do not collect "
            "any personal or sensitive information."
        )
        message_label = QLabel(message_text)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # You could add a link to a privacy policy here
        # privacy_policy_label = QLabel('<a href="https://example.com/privacy">Read our privacy policy</a>')
        # privacy_policy_label.setOpenExternalLinks(True)
        # layout.addWidget(privacy_policy_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.decline_button = QPushButton("Don't Allow")
        self.decline_button.clicked.connect(self.decline)
        button_layout.addWidget(self.decline_button)

        self.accept_button = QPushButton("Allow Anonymous Data")
        self.accept_button.setDefault(True)
        self.accept_button.clicked.connect(self.accept)
        button_layout.addWidget(self.accept_button)

        layout.addLayout(button_layout)

    def accept(self):
        """User agreed to send data."""
        logging.info("User consented to telemetry.")
        db_manager.set_setting('telemetry_consent', 'True')
        super().accept()

    def decline(self):
        """User declined to send data."""
        logging.info("User declined telemetry.")
        db_manager.set_setting('telemetry_consent', 'False')
        super().reject()

    @staticmethod
    def should_show():
        """
        Checks if the consent dialog should be shown.
        It should be shown only if the setting has never been set before.
        """
        consent = db_manager.get_setting('telemetry_consent')
        return consent is None
