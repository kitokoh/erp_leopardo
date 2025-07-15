# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialogButtonBox

class ConfigDialog(QDialog):
    def __init__(self, app_id, config, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.config = config

        self.setWindowTitle(f"Configuration pour {app_id}")
        self.layout = QVBoxLayout(self)

        self.fields = {}
        if self.app_id == "n8n":
            self.add_field("Port", "port", self.config.get("port", "5678"))

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def add_field(self, label_text, key, default_value):
        self.layout.addWidget(QLabel(label_text))
        line_edit = QLineEdit(default_value)
        self.layout.addWidget(line_edit)
        self.fields[key] = line_edit

    def get_config(self):
        for key, field in self.fields.items():
            self.config[key] = field.text()
        return self.config
