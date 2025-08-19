# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QDialogButtonBox, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt

class CompileDocumentsDialog(QDialog):
    def __init__(self, available_documents: list, default_file_name: str, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.available_documents = available_documents # List of dicts {'document_id': ..., 'document_name': ..., 'file_path_abs': ...}

        self.setWindowTitle(self.tr("Compiler des Documents PDF"))
        self.setMinimumWidth(500)

        self._setup_ui(default_file_name)

    def _setup_ui(self, default_file_name: str):
        main_layout = QVBoxLayout(self)

        main_layout.addWidget(QLabel(self.tr("Sélectionnez les documents PDF à inclure dans la compilation :")))

        self.doc_list_widget = QListWidget()
        for doc_info in self.available_documents:
            item_text = f"{doc_info.get('document_name', 'Document Inconnu')} (ID: {doc_info.get('document_id', 'N/A')[:8]}...)"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, doc_info) # Store full info
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked) # Check by default
            self.doc_list_widget.addItem(list_item)
        main_layout.addWidget(self.doc_list_widget)

        main_layout.addWidget(QLabel(self.tr("Nom du fichier pour le document compilé :")))
        self.output_file_name_edit = QLineEdit(default_file_name)
        self.output_file_name_edit.setPlaceholderText(self.tr("Ex: Compilation_Commande_XYZ.pdf"))
        main_layout.addWidget(self.output_file_name_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Compiler"))
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def get_selected_documents_info(self) -> list:
        selected = []
        for i in range(self.doc_list_widget.count()):
            item = self.doc_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected

    def get_output_file_name(self) -> str:
        name = self.output_file_name_edit.text().strip()
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        return name

    def tr(self, text, disambiguation=None, n=-1):
        from PyQt5.QtWidgets import QApplication
        return QApplication.translate("CompileDocumentsDialog", text, disambiguation, n)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    # Exemple de documents
    docs = [
        {'document_id': 'uuid-pdf-1', 'document_name': 'Facture Proforma PF-001.pdf', 'file_path_abs': '/path/to/pf001.pdf'},
        {'document_id': 'uuid-pdf-2', 'document_name': 'Bon de Livraison BL-002.pdf', 'file_path_abs': '/path/to/bl002.pdf'},
        {'document_id': 'uuid-pdf-3', 'document_name': 'Spécifications Techniques Spec-003.pdf', 'file_path_abs': '/path/to/spec003.pdf'}
    ]
    dialog = CompileDocumentsDialog(available_documents=docs, default_file_name="Compilation_Test.pdf")
    if dialog.exec_() == QDialog.Accepted:
        print("Documents sélectionnés:", [doc['document_name'] for doc in dialog.get_selected_documents_info()])
        print("Nom du fichier de sortie:", dialog.get_output_file_name())
    else:
        print("Annulé")
    sys.exit(app.exec_())
