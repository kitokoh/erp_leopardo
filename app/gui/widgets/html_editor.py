import os
import sys
import json # For escaping strings for JavaScript
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QFileDialog, QStyle, QLabel, QLineEdit, QWidget,
    QSizePolicy, QSplitter
)
from PyQt5.QtWebChannel import QWebChannel

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QStandardPaths, Qt, QCoreApplication, pyqtSlot, QObject, pyqtSignal, QFileInfo, QTimer
import db as db_manager # Assuming db_manager provides necutils.
from db.db_utils import get_document_context_data
# from db.cruds.companies_crud import get_default_company # Moved into __init__
from utils.html_to_pdf_util import render_html_template, convert_html_to_pdf

class JsBridge(QObject):
    editorContentReady = pyqtSignal(str)
    tinymceInitialized = pyqtSignal()

    def __init__(self, editor_instance):
        super().__init__()
        self.editor = editor_instance

    @pyqtSlot(str)
    def receiveHtmlContent(self, html):
        self.editor.raw_html_content_from_editor = html
        self.editorContentReady.emit(html)

    @pyqtSlot()
    def onTinymceInitialized(self):
        print("TinyMCE initialized (signal from JS)")
        self.tinymceInitialized.emit()


class HtmlEditor(QDialog):
    def __init__(self, file_path: str, client_data: dict, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.client_data = client_data
        self._current_pdf_export_path = None
        self.raw_html_content_from_editor = ""
        self.target_language_code = "fr" # Default language for preview context

        self.web_view = None
        self.bridge = None
        self.channel = None
        self.tinymce_init_timer = None

        from db.cruds.companies_crud import get_default_company # Deferred import
        default_company_obj = get_default_company()
        self.default_company_id = default_company_obj['company_id'] if default_company_obj else None
        if not self.default_company_id:
            print("WARNING: No default company found. Seller details may be missing for preview.")

        # Extract target_language_code from file_path for preview context
        if self.file_path and os.path.exists(self.file_path):
            try:
                # Assumes path structure like .../base_folder/lang_code/filename.html
                lang_from_path = os.path.basename(os.path.dirname(self.file_path))
                # Basic validation if it's a known lang code
                if lang_from_path in ["en", "fr", "ar", "tr", "pt"]: # Add other supported codes
                    self.target_language_code = lang_from_path
                    print(f"HtmlEditor: Target language for preview set to '{self.target_language_code}' from file path.")
                else:
                    print(f"Warning: HtmlEditor extracted language '{lang_from_path}' from path is not standard, defaulting to '{self.target_language_code}' for preview.")
            except Exception as e_path:
                print(f"HtmlEditor: Could not extract language from path '{self.file_path}', defaulting to '{self.target_language_code}' for preview. Error: {e_path}")
        else:
            print(f"HtmlEditor: file_path not provided or does not exist, defaulting to '{self.target_language_code}' for preview.")

        self._setup_ui()
        if self.bridge:
            self.bridge.tinymceInitialized.connect(self._load_file_content_into_tinymce)

        # Timer for TinyMCE initialization
        self.tinymce_init_timer = QTimer(self)
        self.tinymce_init_timer.setSingleShot(True)
        self.tinymce_init_timer.timeout.connect(self._handle_tinymce_init_timeout)

    def _setup_ui(self):
        # Window title is set by caller if file_path is None (e.g. HtmlTemplateCreatorDialog)
        # or here if file_path is provided (editing existing)
        if self.file_path:
            self.setWindowTitle(self.tr("HTML Editor (TinyMCE) - {0}").format(os.path.basename(self.file_path)))
        else:
            # Title will be set by the calling dialog like HtmlTemplateCreatorDialog
            # Or we can set a generic one here if preferred for direct instantiation without path.
            self.setWindowTitle(self.tr("HTML Editor (TinyMCE) - New Document"))

        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)

        self.preview_pane = QWebEngineView()
        splitter.addWidget(self.preview_pane)

        splitter.setSizes([700, 500])
        main_layout.addWidget(splitter, 1)

        self.bridge = JsBridge(self)
        self.channel = QWebChannel(self.web_view.page())
        self.web_view.page().setWebChannel(self.channel)
        self.channel.registerObject("qt_bridge", self.bridge)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        loader_html_path = os.path.join(current_dir, "html_editor_assets", "tinymce_loader.html")

        if not os.path.exists(loader_html_path):
            error_msg = f"tinymce_loader.html not found at {loader_html_path}. WYSIWYG editor cannot load."
            QMessageBox.critical(self, "Error", error_msg)
            self.web_view.setHtml(f"<h1>{error_msg}</h1>")
        else:
            fi = QFileInfo(loader_html_path)
            self.web_view.setUrl(QUrl.fromLocalFile(fi.absoluteFilePath()))

        self.web_view.loadFinished.connect(self._on_web_view_load_finished)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton(self.tr("Save"))
        self.save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.refresh_button = QPushButton(self.tr("Refresh Preview"))
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.export_pdf_button = QPushButton(self.tr("Export to PDF"))
        self.export_pdf_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogToParent))
        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_pdf_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.save_content)
        self.refresh_button.clicked.connect(self.refresh_preview)
        self.export_pdf_button.clicked.connect(self.export_to_pdf)
        self.close_button.clicked.connect(self.reject)
        self.bridge.editorContentReady.connect(self._handle_editor_content_callback)

    def _on_web_view_load_finished(self, success):
        if success:
            print("WebEngineView (loader) finished loading.")
            # Start timer to check if TinyMCE initializes
            self.tinymce_init_timer.start(7000) # 7 seconds timeout
        else:
            QMessageBox.critical(self, "Load Error", "Failed to load the TinyMCE loader HTML.")
            # Consider closing or disabling the editor if the loader itself fails.

    def _load_file_content_into_tinymce(self):
        self.tinymce_init_timer.stop() # TinyMCE has initialized (or at least JS bridge called us)
        print("Attempting to load content into TinyMCE...")
        content_to_load = ""
        if self.file_path and os.path.exists(self.file_path):  # 8 spaces
            try:  # 12 spaces
                with open(self.file_path, 'r', encoding='utf-8') as f:  # 16 spaces
                    content_to_load = f.read()  # 20 spaces
            except IOError as e:  # 12 spaces
                QMessageBox.warning(self, self.tr("Load Error"), f"Could not load HTML file: {self.file_path}\n{e}")  # 16 spaces
                content_to_load = self._get_default_skeleton_html()  # 16 spaces
        else:  # 8 spaces
            content_to_load = self._get_default_skeleton_html()  # 12 spaces

        escaped_content = json.dumps(content_to_load)
        self.web_view.page().runJavaScript(f"setEditorContent({escaped_content});")
        self.raw_html_content_from_editor = content_to_load
        self.refresh_preview()


    def _get_default_skeleton_html(self):
        # A more comprehensive default skeleton for new templates
        return """<!DOCTYPE html>
<html lang="{{ doc.language_code | default('en') }}">
<head>
    <meta charset="UTF-8">
    <title>{{ client.name | default('N/A') }} - {{ doc.type | default('Document') }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
        .header { background-color: #f2f2f2; padding: 10px; text-align: center; }
        .content { margin-top: 20px; }
        .footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 0.9em; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ seller.name | default('Your Company') }}</h1>
        <p>{{ seller.address_raw | default('Your Company Address') }}</p>
    </div>

    <div class="content">
        <h2>{{ doc.type | default('Document Title') }}</h2>
        <p><strong>Date:</strong> {{ doc.current_date }}</p>
        <p><strong>Client:</strong> {{ client.name | default('Client Name') }}</p>
        <p><strong>Client Address:</strong> {{ client.full_address | default('Client Address') }}</p>

        <p>Dear {{ client.contact_name | default('Client Contact') }},</p>
        <p>This is a placeholder for your document content. You can use Jinja2 templating for dynamic data.</p>

        {{#if products}}
        <h3>Products/Services:</h3>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total Price</th>
                </tr>
            </thead>
            <tbody>
                {{#each products}}
                <tr>
                    <td>{{ this.name }}</td>
                    <td>{{ this.description }}</td>
                    <td>{{ this.quantity_formatted }}</td>
                    <td>{{ this.price_formatted }}</td>
                    <td>{{ this.total_price_formatted }}</td>
                </tr>
                {{/each}}
            </tbody>
        </table>
        {{else}}
        <p><em>No products listed for this document.</em></p>
        {{/if}}

        <p>Further details and terms can be added here.</p>
    </div>

    <div class="footer">
        <p>&copy; {{ doc.current_year }} {{ seller.name | default('Your Company') }}. All rights reserved.</p>
        <p>Thank you for your business!</p>
    </div>
</body>
</html>"""

    def _replace_placeholders_html(self, html_content: str) -> str:
        # Ensure client_data is present, even if it's just dummy data for new templates
        if not self.client_data: # Should typically be provided, even if dummy
            print("HtmlEditor Warning: client_data is missing. Preview might be incomplete.")
            # Create a minimal dummy client_data if it's absolutely missing, to avoid crashing get_document_context_data
            temp_dummy_client_data = {'client_id': 'dummy_preview_id_if_missing'}
        else:
            temp_dummy_client_data = self.client_data

        # Ensure client_id is in the (potentially dummy) client_data for context fetching
        if 'client_id' not in temp_dummy_client_data:
            # This situation implies an issue with how client_data is passed or constructed.
            # For robustness in preview, we'll add a placeholder.
            print("HtmlEditor Warning: 'client_id' missing in client_data for preview. Using placeholder.")
            temp_dummy_client_data['client_id'] = 'placeholder_client_id_for_preview'


        client_id_for_context = temp_dummy_client_data.get('client_id')
        project_id_for_context = temp_dummy_client_data.get('project_id_db_uuid', temp_dummy_client_data.get('project_identifier'))

        try:
            context = get_document_context_data(
                client_id=client_id_for_context,
                company_id=self.default_company_id,
                target_language_code=self.target_language_code,
                project_id=project_id_for_context if project_id_for_context else None,
                additional_context=temp_dummy_client_data # Use the potentially augmented temp_dummy_client_data
            )

            # Optional: "No Products" check for preview (console warning only)
            # Use self.file_path if available, otherwise a generic name for new documents
            doc_name_for_check = os.path.basename(self.file_path) if self.file_path else "new_document.html"
            doc_name_for_check = doc_name_for_check.lower()

            if "proforma" in doc_name_for_check or "invoice" in doc_name_for_check:
                products_in_target_lang = [p for p in context.get('products', []) if p.get('is_language_match')]
                if not context.get('products'):
                    print(f"HtmlEditor Preview Info: No products linked for document '{doc_name_for_check}'.")
                elif not products_in_target_lang:
                    print(f"HtmlEditor Preview Info: No products found in language '{self.target_language_code}' for document '{doc_name_for_check}'.")

            return render_html_template(html_content, context)
        except Exception as e:
            print(f"Error during placeholder replacement for preview: {e}")
            QMessageBox.critical(self, self.tr("Template Error"), self.tr("Could not process template placeholders for preview: {0}").format(e))
            return html_content

    _save_pending = False
    _preview_pending = False
    _export_pdf_pending = False

    def _handle_editor_content_callback(self, html_content):
        self.raw_html_content_from_editor = html_content

        if self._save_pending:
            self._save_pending = False
            if not self.file_path:
                # This is a new template being created.
                # The HtmlTemplateCreatorDialog will handle the actual file and DB saving.
                # Here, we just accept the dialog so HtmlTemplateCreatorDialog can get raw_html_content_from_editor.
                # A check for empty content can be good.
                if not self.raw_html_content_from_editor.strip():
                    QMessageBox.warning(self, self.tr("Empty Content"), self.tr("Cannot save an empty template. Please add some content."))
                    return # Stay in editor
                self.accept() # Signal to calling dialog (HtmlTemplateCreatorDialog) that content is ready
                return

            # Existing file path, save normally
            try:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(self.raw_html_content_from_editor)
                QMessageBox.information(self, self.tr("Success"), self.tr("HTML content saved successfully to {0}.").format(self.file_path))
                # No need to change window title here if it was already set correctly
                self.accept() # Close editor on successful save
            except IOError as e:
                QMessageBox.critical(self, self.tr("Save Error"), self.tr("Could not save HTML file: {0}\n{1}").format(self.file_path, e))

        elif self._preview_pending:
            self._preview_pending = False
            processed_html = self._replace_placeholders_html(self.raw_html_content_from_editor)
            base_url = QUrl.fromLocalFile(QFileInfo(self.file_path).absolutePath()) if self.file_path and os.path.exists(self.file_path) else QUrl()
            self.preview_pane.setHtml(processed_html, baseUrl=base_url)

        elif self._export_pdf_pending:
            self._export_pdf_pending = False
            self._actual_export_to_pdf()

    def save_content(self):
        self._save_pending = True
        self._preview_pending = False
        self._export_pdf_pending = False
        self.web_view.page().runJavaScript("getEditorContent();")

    def refresh_preview(self):
        self._preview_pending = True
        self._save_pending = False
        self._export_pdf_pending = False
        self.web_view.page().runJavaScript("getEditorContent();")

    def export_to_pdf(self):
        self._export_pdf_pending = True
        self._save_pending = False
        self._preview_pending = False
        self.web_view.page().runJavaScript("getEditorContent();")

    def _actual_export_to_pdf(self):
        if not self.raw_html_content_from_editor:
            QMessageBox.warning(self, self.tr("No Content"), self.tr("Editor content is empty. Cannot export PDF."))
            return

        default_file_name = os.path.splitext(os.path.basename(self.file_path or "document"))[0] + ".pdf"
        default_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), default_file_name)

        file_path_pdf, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save PDF As"), default_path, self.tr("PDF Files (*.pdf)")
        )

        if file_path_pdf:
            processed_html_for_pdf = self._replace_placeholders_html(self.raw_html_content_from_editor)
            base_url_for_pdf = QUrl.fromLocalFile(QFileInfo(self.file_path).absolutePath()).toString() if self.file_path and os.path.exists(self.file_path) else None

            pdf_bytes = convert_html_to_pdf(processed_html_for_pdf, base_url=base_url_for_pdf)
            if pdf_bytes:
                try:
                    with open(file_path_pdf, 'wb') as f:
                        f.write(pdf_bytes)
                    QMessageBox.information(self, self.tr("PDF Export"), self.tr("PDF exported successfully to: {0}").format(file_path_pdf))
                except IOError as e:
                    QMessageBox.critical(self, self.tr("PDF Export Error"), self.tr("Could not save PDF file: {0}\n{1}").format(file_path_pdf, e))
            else:
                 QMessageBox.warning(self, self.tr("PDF Export Error"), self.tr("Failed to generate PDF content."))

    @staticmethod
    def populate_html_content(html_template_content: str, document_context: dict) -> str:
        """
        Populates HTML content using a pre-constructed document_context.
        This method is intended for use by external callers like PDF generation utilities.
        """
        if not document_context:
            print("Static Populate Error: document_context is missing or empty.")
            # Consider returning html_template_content or raising an error
            return html_template_content
        try:
            # The document_context is now expected to be fully resolved by the caller
            # (e.g., utils.generate_pdf_for_document which calls db.get_document_context_data)
            return render_html_template(html_template_content, document_context)
        except Exception as e:
            print(f"Error in static populate_html_content with pre-built context: {e}")
            # Potentially log the context for debugging, carefully avoiding sensitive data in logs
            # print(f"Context was: {str(document_context)[:500]}...")
            return html_template_content # Return original content on error

    def _handle_tinymce_init_timeout(self):
        if not self.web_view: # Should not happen if timer was started
            return

        # Check if TinyMCE might have initialized right before timeout (less likely but good practice)
        # This check is a bit indirect; assumes if JS called onTinymceInitialized, _load_file_content_into_tinymce would have stopped the timer.
        # If the timer is still running, it means onTinymceInitialized was not called.
        if self.tinymce_init_timer.isActive(): # Ensure it's genuinely a timeout
            self.tinymce_init_timer.stop() # Stop it just in case

            error_title = self.tr("TinyMCE Failed to Initialize")
            error_message = self.tr(
                "The rich text editor (TinyMCE) could not be loaded. "
                "This is often due to missing TinyMCE library files. "
                "Please ensure the TinyMCE library is correctly placed in the "
                "'html_editor_assets/tinymce' directory. You may need to download "
                "it from the official TinyMCE website.\n\n"
                "The editor may not function correctly or will now close."
            )
            QMessageBox.critical(self, error_title, error_message)
            self.web_view.setHtml(f"<h1>{error_title}</h1><p>{error_message}</p>") # Show error in web view
            # Optionally, disable functions or close
            self.save_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.export_pdf_button.setEnabled(False)
            # self.reject() # Or, to close the dialog immediately


if __name__ == '__main__':
    # Required for QWebEngineView
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    dummy_client_data = {
        "client_id": "dummy_client_uuid_123",
        "Nom du client": "Client Test Main",
        "project_identifier": "MAIN_PROJ_001",
        "Besoin": "Testing Main Application Flow",
        "price": 123.45,
    }

    class MockDBForMain:
        def __init__(self):
            print("Using MockDBForMain for html_editor.py's __main__ block.")

        def get_default_company(self):
            print("MockDB: get_default_company called")
            return {"company_id": "dummy_company_uuid_456", "company_name": "Mock Default Corp"}

        def get_document_context_data(self, client_id, company_id, project_id=None, product_ids=None, additional_context=None):
            print(f"MockDB: get_document_context_data called with client_id={client_id}, company_id={company_id}, project_id={project_id}")
            mock_context = {
                "doc": {
                    "current_date": datetime.now().strftime("%Y-%m-%d"),
                    "current_year": str(datetime.now().year),
                    "currency_symbol": "$",
                    "show_products": True
                },
                "client": {
                    "name": dummy_client_data.get("Nom du client", "N/A Client from Mock"),
                    "id": client_id,
                    "full_address": "Mock Client Address, Mock City, Mock Country",
                    "contact_name": "Mock Client Contact"
                },
                "seller": {
                    "name": "Mock Default Corp from Mock",
                    "address_raw": "Mock Seller St, Seller City",
                    "logo_path_absolute": None
                },
                "seller_personnel": {
                    "sales_person_name": "Mock Sales Person"
                },
                "project": {
                    "name": project_id if project_id else "N/A Project from Mock",
                    "id": project_id
                },
                "products": [
                    {"name": "Mock Product A", "price_formatted": "$100", "description": "Desc A"},
                    {"name": "Mock Product B", "price_formatted": "$200", "description": "Desc B"}
                ] if project_id else [],
                "additional": {}
            }
            if additional_context:
                mock_context["additional"].update(additional_context)
            return mock_context

        def get_setting(self, key, default=""):
            print(f"MockDB: get_setting called for {key}")
            return f"MockSetting: {key}"


    original_db_module = sys.modules['db']
    mock_db_instance = MockDBForMain()

    original_get_default_company = db_manager.get_default_company
    original_get_document_context_data = db_manager.get_document_context_data

    db_manager.get_default_company = mock_db_instance.get_default_company
    db_manager.get_document_context_data = mock_db_instance.get_document_context_data

    temp_dir = QStandardPaths.writableLocation(QStandardPaths.TemporaryLocation)
    os.makedirs(temp_dir, exist_ok=True)
    dummy_file_name = f"test_editor_doc_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    dummy_file_path = os.path.join(temp_dir, dummy_file_name)
    print(f"Test HTML file will be at: {dummy_file_path}")

    with open(dummy_file_path, 'w', encoding='utf-8') as f_dummy:
        f_dummy.write("""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{{doc.current_date}} - {{client.name}}</title>
</head>
<body>
    <h1>Client: {{client.name}}</h1>
    <p>Address: {{client.full_address}}</p>
    <p>Contact: {{client.contact_name}}</p>
    <hr>
    <h2>Vendeur: {{seller.name}}</h2>
    <p>Vendeur (Commercial): {{seller_personnel.sales_person_name}}</p>
    <p>Projet: {{project.name}} (ID: {{project.id}})</p>

    {{#if doc.show_products}}
        <h3>Produits:</h3>
        <ul>
            {{#each products}}
            <li>{{this.name}} - {{this.price_formatted}} -- {{this.description}}</li>
            {{/each}}
        </ul>
    {{/if}}
    <p>Document généré le: {{doc.current_date}}. Année: {{doc.current_year}}.</p>
</body>
</html>""")

    editor = HtmlEditor(file_path=dummy_file_path, client_data=dummy_client_data)
    editor.show()
    app_exit_code = app.exec_()

    db_manager.get_default_company = original_get_default_company
    db_manager.get_document_context_data = original_get_document_context_data

    sys.exit(app_exit_code)
