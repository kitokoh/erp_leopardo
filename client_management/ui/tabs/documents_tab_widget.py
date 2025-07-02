# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget, QPushButton, QAbstractItemView, QHeaderView, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Globals imported from main (temporary, to be refactored or passed)
# from main import SUPPORTED_LANGUAGES # Assuming this will be passed or accessed via config

class DocumentsTabWidget(QWidget):
    def __init__(self, client_info, config, current_user_info, parent_client_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.current_user_info = current_user_info
        self.parent_client_widget = parent_client_widget # For actions, dialogs, notifications

        self.layout = QVBoxLayout(self)
        self._setup_ui()

# Globals imported from main (temporary, to be refactored or passed)
SUPPORTED_LANGUAGES = ["en", "fr", "ar", "tr", "pt", "ru"] # Define supported languages

class DocumentsTabWidget(QWidget):
    def __init__(self, client_info, config, current_user_info, parent_client_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.current_user_info = current_user_info
        self.parent_client_widget = parent_client_widget # For actions, dialogs, notifications
        self.tr = self.parent_client_widget.tr if hasattr(self.parent_client_widget, 'tr') else lambda x: x

        self.layout = QVBoxLayout(self)
        self._setup_ui()
        # Initial data population will be triggered by parent_client_widget after all tabs are set up,
        # by calling a method like self.documents_tab_widget_instance.populate_documents()

    def _setup_ui(self):
        self.doc_filter_layout_widget = QWidget()
        doc_filter_layout = QHBoxLayout(self.doc_filter_layout_widget)
        doc_filter_layout.setContentsMargins(0,0,0,0)

        doc_filter_label = QLabel(self.tr("Filtrer par Commande:"))
        doc_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_filter_label)

        self.doc_order_filter_combo = QComboBox()
        self.doc_order_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_order_filter_combo.currentIndexChanged.connect(self.parent_client_widget.populate_doc_table) # Connect to parent's method for now
        doc_filter_layout.addWidget(self.doc_order_filter_combo)
        doc_filter_layout.addSpacing(10)

        doc_lang_filter_label = QLabel(self.tr("Filtrer par Langue:"))
        doc_lang_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_lang_filter_label)

        self.doc_language_filter_combo = QComboBox()
        self.doc_language_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_language_filter_combo.addItem(self.tr("Toutes"), "ALL")
        for lang_code in SUPPORTED_LANGUAGES: # Assuming SUPPORTED_LANGUAGES is available
            self.doc_language_filter_combo.addItem(lang_code, lang_code)
        self.doc_language_filter_combo.currentIndexChanged.connect(self.parent_client_widget.populate_doc_table) # Connect to parent
        doc_filter_layout.addWidget(self.doc_language_filter_combo)
        doc_filter_layout.addSpacing(10)

        doc_type_filter_label = QLabel(self.tr("Filtrer par Type:"))
        doc_type_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_type_filter_label)

        self.doc_type_filter_combo = QComboBox()
        self.doc_type_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_type_filter_combo.addItem(self.tr("Tous"), "ALL")
        self.doc_type_filter_combo.addItem("HTML", "HTML")
        self.doc_type_filter_combo.addItem("PDF", "PDF")
        self.doc_type_filter_combo.addItem("XLSX", "XLSX")
        self.doc_type_filter_combo.addItem("DOCX", "DOCX")
        self.doc_type_filter_combo.addItem(self.tr("Autre"), "OTHER")
        self.doc_type_filter_combo.currentIndexChanged.connect(self.parent_client_widget.populate_doc_table) # Connect to parent
        doc_filter_layout.addWidget(self.doc_type_filter_combo)

        # "Combiné" (Compile PDF) button
        # Assuming parent_client_widget.compile_pdf_btn is the one to be reused or a new one is made here.
        # For simplicity, we refer to the parent's existing button instance if it's meant to be shared.
        if hasattr(self.parent_client_widget, 'compile_pdf_btn'):
            self.combine_docs_btn = self.parent_client_widget.compile_pdf_btn
            self.combine_docs_btn.setText(self.tr("Combiné")) # Update text if needed
            self.combine_docs_btn.setIcon(QIcon.fromTheme("document-export", QIcon(":/icons/folder.svg")))
            self.combine_docs_btn.setToolTip(self.tr("Combiner plusieurs documents PDF"))
            # Connection is already on parent_client_widget.compile_pdf_btn
            doc_filter_layout.addWidget(self.combine_docs_btn)
        else: # Fallback: Create a new button specific to this tab
            self.combine_docs_btn = QPushButton(self.tr("Combiné"))
            self.combine_docs_btn.setIcon(QIcon.fromTheme("document-export", QIcon(":/icons/folder.svg")))
            self.combine_docs_btn.setToolTip(self.tr("Combiner plusieurs documents PDF"))
            self.combine_docs_btn.clicked.connect(self.parent_client_widget.open_compile_pdf_dialog)
            doc_filter_layout.addWidget(self.combine_docs_btn)

        self.plus_add_doc_btn = QPushButton("+")
        self.plus_add_doc_btn.setToolTip(self.tr("Ajouter un document (depuis modèle ou importation directe)"))
        self.plus_add_doc_btn.setFixedSize(30, 30)
        self.plus_add_doc_btn.clicked.connect(self.parent_client_widget.handle_plus_add_doc_button_click)
        doc_filter_layout.addWidget(self.plus_add_doc_btn)
        doc_filter_layout.addStretch(1)

        self.layout.addWidget(self.doc_filter_layout_widget)
        self.doc_filter_layout_widget.setVisible(True)

        self.documents_empty_label = QLabel(self.tr("Aucun document trouvé pour ce client.\nUtilisez les boutons ci-dessous pour ajouter ou générer des documents."))
        self.documents_empty_label.setAlignment(Qt.AlignCenter)
        font_docs_empty = self.documents_empty_label.font()
        font_docs_empty.setPointSize(10)
        self.documents_empty_label.setFont(font_docs_empty)
        self.layout.addWidget(self.documents_empty_label)

        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(6) # Name, Type, Language, Date, Original File, Quick Actions
        self.doc_table.setHorizontalHeaderLabels([
            self.tr("Nom"), self.tr("Type"), self.tr("Langue"),
            self.tr("Date"), self.tr("Fichier Original"), self.tr("Actions Rapides")
        ])
        self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Name
        for i in range(1, 6): # Type, Lang, Date, Original File, Quick Actions
             self.doc_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.layout.addWidget(self.doc_table)

        doc_btn_layout = QHBoxLayout()
        self.add_doc_btn = QPushButton(self.tr("Importer Document"))
        self.add_doc_btn.setIcon(QIcon(":/icons/file-plus.svg"))
        self.add_doc_btn.setToolTip(self.tr("Importer un fichier document existant pour ce client"))
        self.add_doc_btn.clicked.connect(self.parent_client_widget.add_document)
        doc_btn_layout.addWidget(self.add_doc_btn)

        self.refresh_docs_btn = QPushButton(self.tr("Actualiser"))
        self.refresh_docs_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_docs_btn.clicked.connect(self.parent_client_widget.populate_doc_table)
        doc_btn_layout.addWidget(self.refresh_docs_btn)

        self.add_template_btn = QPushButton(self.tr("Générer via Modèle"))
        self.add_template_btn.setIcon(QIcon.fromTheme("document-new", QIcon(":/icons/file-plus.svg")))
        self.add_template_btn.setToolTip(self.tr("Générer un nouveau document pour ce client à partir d'un modèle"))
        self.add_template_btn.clicked.connect(self.parent_client_widget.open_create_docs_dialog)
        doc_btn_layout.addWidget(self.add_template_btn)

        self.layout.addLayout(doc_btn_layout)

    def populate_documents_table_data(self, documents_data, base_client_path):
        """
        Populates the self.doc_table with the provided documents_data.
        This method is intended to be called by ClientWidget after fetching and filtering data.
        The base_client_path is the absolute path to the client's main document folder.
        """
        self.doc_table.setRowCount(0) # Clear existing rows
        if not documents_data:
            self.documents_empty_label.setVisible(True)
            self.doc_table.setVisible(False)
            return

        self.documents_empty_label.setVisible(False)
        self.doc_table.setVisible(True)
        self.doc_table.setRowCount(len(documents_data))

        for row_idx, doc_data in enumerate(documents_data):
            # Delegate actual row population to parent_client_widget to keep logic centralized
            # This is a temporary measure until all document-related logic is moved.
            # Ideally, DocumentsTabWidget would handle this itself.
            self.parent_client_widget._populate_doc_table_row(self.doc_table, row_idx, doc_data, base_client_path)

    # Other methods like handle_plus_add_doc_button_click, add_document, etc.,
    # will either be moved here entirely (if they don't depend too much on ClientWidget's direct state)
    # or will remain in ClientWidget and be called via self.parent_client_widget.
    # For UI-specific actions that trigger dialogs, it's common to call methods on the parent.
