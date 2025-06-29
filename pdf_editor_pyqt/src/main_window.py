import sys
import fitz  # PyMuPDF
import logging 
import os 

from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QMenu, QMenuBar, 
                             QToolBar, QDockWidget, QLabel, QWidget, 
                             QListWidget, QListWidgetItem, QTextEdit, QFileDialog, QMessageBox,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QPushButton, QHBoxLayout, QSpinBox, QScrollArea,
                             QColorDialog, QInputDialog, QLineEdit, QCheckBox,
                             QRadioButton, QVBoxLayout, QButtonGroup, QComboBox,
                             QDialog, QVBoxLayout as QDialogVBoxLayout, QTextEdit as QDialogTextEdit, 
                             QPushButton as QDialogButton, QHBoxLayout as QDialogHBoxLayout, 
                             QAbstractItemView, QFormLayout, QTreeWidget, QTreeWidgetItem) 
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF, QLineF, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QImage, QColor, QPen, QPainterPath, QMouseEvent

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

class TextDisplayDialog(QDialog):
    def __init__(self, text_content, title="Texte Extrait", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        layout = QDialogVBoxLayout(self)
        self.text_edit = QDialogTextEdit(self)
        self.text_edit.setPlainText(text_content)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        button_layout = QHBoxLayout()
        self.copy_button = QDialogButton("Copier dans le Presse-papiers", self)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_button)
        self.save_button = QDialogButton("Enregistrer sous...", self)
        self.save_button.clicked.connect(self.save_text_to_file)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "Copié", "Texte copié.")
    def save_text_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le texte", "", "Fichiers Texte (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f: f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "Enregistré", f"Texte enregistré: {file_path}")
            except Exception as e: QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

class PageRangeDialog(QDialog):
    def __init__(self, total_pages, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Définir les Plages de Pages")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        
        self.instruction_label = QLabel("Entrez les plages de pages (ex: 1-3, 5, 7-fin):")
        layout.addWidget(self.instruction_label)
        
        self.range_input_line_edit = QLineEdit(self)
        self.range_input_line_edit.setObjectName("range_input_line_edit")
        layout.addWidget(self.range_input_line_edit)
        
        self.total_pages_label = QLabel(f"Le document a {total_pages} page(s).")
        self.total_pages_label.setObjectName("total_pages_label")
        layout.addWidget(self.total_pages_label)
        
        # Boutons OK et Annuler
        button_box = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Annuler", self)
        self.cancel_button.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)
        layout.addLayout(button_box)

    def get_range_string(self):
        return self.range_input_line_edit.text()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Initialisation de MainWindow.")
        self.setWindowTitle("Éditeur PDF PyQt")
        self.setGeometry(100, 100, 1200, 800)
        self.current_pdf_document = None
        self.current_page_number = 0
        self.current_zoom_factor = 1.0
        self.is_document_modified = False
        self.current_tool_mode = "pointer" 
        self.highlight_color = (1, 1, 0) 
        self.ink_color = (0, 0, 1) 
        self.ink_thickness = 1.5 
        self.shape_border_color = (1, 0, 0) 
        self.shape_fill_color = None 
        self.shape_border_width = 1.5
        self.freetext_fontname = "helv" 
        self.freetext_fontsize = 11
        self.freetext_color = (0,0,0) 
        self.selection_start_point = None 
        self.selection_rect_item = None 
        self.current_ink_stroke = [] 
        self.temp_ink_item = None 
        self.selected_annotation = None 
        self.selected_annotation_bbox_item = None 
        self.selected_widget = None 
        self.property_widget_layout = None 
        self.current_prop_widgets = [] 
        self.pending_redactions = [] # For QRectF in scene coords
        self.pending_redaction_items = [] # For QGraphicsRectItems on scene
        # Redaction appearance attributes
        self.redaction_fill_color = (0, 0, 0)  # Default black
        self.redaction_overlay_text = ""
        self.redaction_text_color = (1, 1, 1)  # Default white
        self.redaction_fontname = "helv"       # Default Helvetica
        self.redaction_fontsize = 0            # Default auto-size
        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bars()
        self._setup_central_widget() 
        self._create_dock_widgets() 
        self._create_navigation_bar()
        self._update_tool_mode_ui(None) 
        self.statusBar().showMessage("Prêt")

    def _create_actions(self):
        # ... (Actions existantes) ...
        self.open_action = QAction(QIcon.fromTheme("document-open", QIcon(":/icons/document-open.png")), "&Ouvrir...", self)
        self.open_action.triggered.connect(self.open_file)
        self.save_action = QAction(QIcon.fromTheme("document-save", QIcon(":/icons/document-save.png")), "&Enregistrer", self)
        self.save_action.triggered.connect(self.save_file); self.save_action.setEnabled(False)
        self.save_as_action = QAction(QIcon.fromTheme("document-save-as", QIcon(":/icons/document-save-as.png")), "Enregistrer &sous...", self)
        self.save_as_action.triggered.connect(self.save_file_as); self.save_as_action.setEnabled(False)
        self.exit_action = QAction(QIcon.fromTheme("application-exit", QIcon(":/icons/application-exit.png")), "&Quitter", self)
        self.exit_action.triggered.connect(self.close)
        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon(":/icons/zoom-in.png")), "Zoom &Avant", self)
        self.zoom_in_action.triggered.connect(lambda: self.zoom(1.2)); self.zoom_in_action.setEnabled(False)
        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon(":/icons/zoom-out.png")), "Zoom &Arrière", self)
        self.zoom_out_action.triggered.connect(lambda: self.zoom(0.8)); self.zoom_out_action.setEnabled(False)
        self.zoom_original_action = QAction(QIcon.fromTheme("zoom-original", QIcon(":/icons/zoom-original.png")), "Zoom &Original", self)
        self.zoom_original_action.triggered.connect(lambda: self.set_zoom_factor(1.0)); self.zoom_original_action.setEnabled(False)
        self.prev_page_action = QAction(QIcon.fromTheme("go-previous", QIcon(":/icons/go-previous.png")), "Page &Précédente", self)
        self.prev_page_action.triggered.connect(self.go_to_previous_page); self.prev_page_action.setEnabled(False)
        self.next_page_action = QAction(QIcon.fromTheme("go-next", QIcon(":/icons/go-next.png")), "Page &Suivante", self)
        self.next_page_action.triggered.connect(self.go_to_next_page); self.next_page_action.setEnabled(False)
        self.delete_page_action = QAction(QIcon.fromTheme("edit-delete", QIcon(":/icons/edit-delete.png")), "&Supprimer la Page", self)
        self.delete_page_action.triggered.connect(self.delete_current_page); self.delete_page_action.setEnabled(False)
        self.insert_blank_page_action = QAction(QIcon.fromTheme("document-new", QIcon(":/icons/document-new.png")), "&Insérer Page Vierge...", self)
        self.insert_blank_page_action.triggered.connect(self.insert_blank_page); self.insert_blank_page_action.setEnabled(False)
        self.import_pages_action = QAction(QIcon.fromTheme("document-import", QIcon(":/icons/document-import.png")), "I&mporter Pages depuis PDF...", self)
        self.import_pages_action.triggered.connect(self.import_pages_from_pdf); self.import_pages_action.setEnabled(False)
        self.rotate_cw_action = QAction(QIcon.fromTheme("object-rotate-right", QIcon(":/icons/object-rotate-right.png")), "Rotation Horaire (90°)", self)
        self.rotate_cw_action.triggered.connect(lambda: self.rotate_current_page(90)); self.rotate_cw_action.setEnabled(False)
        self.rotate_ccw_action = QAction(QIcon.fromTheme("object-rotate-left", QIcon(":/icons/object-rotate-left.png")), "Rotation Anti-horaire (90°)", self)
        self.rotate_ccw_action.triggered.connect(lambda: self.rotate_current_page(-90)); self.rotate_ccw_action.setEnabled(False)
        self.crop_page_action = QAction(QIcon.fromTheme("transform-crop", QIcon(":/icons/transform-crop.png")), "&Rogner la Page...", self)
        self.crop_page_action.triggered.connect(self.crop_current_page); self.crop_page_action.setEnabled(False)
        self.highlight_action = QAction(QIcon.fromTheme("format-text-highlight", QIcon(":/icons/format-text-highlight.png")), "&Surligner Texte", self)
        self.highlight_action.setCheckable(True); self.highlight_action.triggered.connect(self.toggle_highlight_mode); self.highlight_action.setEnabled(False)
        self.set_highlight_color_action = QAction(QIcon.fromTheme("format-stroke-color", QIcon(":/icons/color-picker.png")), "Couleur de Surlignage...", self) 
        self.set_highlight_color_action.triggered.connect(self.set_highlight_color); self.set_highlight_color_action.setEnabled(False)
        self.ink_action = QAction(QIcon.fromTheme("draw-freehand", QIcon(":/icons/draw-freehand.png")), "&Dessin (Stylo)", self)
        self.ink_action.setCheckable(True); self.ink_action.triggered.connect(self.toggle_ink_mode); self.ink_action.setEnabled(False)
        self.set_ink_color_action = QAction(QIcon.fromTheme("preferences-color", QIcon(":/icons/ink-color.png")), "Couleur du Stylo...", self) 
        self.set_ink_color_action.triggered.connect(self.set_ink_color); self.set_ink_color_action.setEnabled(False)
        self.set_ink_thickness_action = QAction(QIcon.fromTheme("preferences-line-width", QIcon(":/icons/ink-thickness.png")), "Épaisseur du Stylo...", self) 
        self.set_ink_thickness_action.triggered.connect(self.set_ink_thickness); self.set_ink_thickness_action.setEnabled(False)
        self.rect_annot_action = QAction(QIcon.fromTheme("draw-rectangle", QIcon(":/icons/draw-rectangle.png")), "Dessiner &Rectangle", self)
        self.rect_annot_action.setCheckable(True); self.rect_annot_action.triggered.connect(self.toggle_rect_annot_mode); self.rect_annot_action.setEnabled(False)
        self.circle_annot_action = QAction(QIcon.fromTheme("draw-ellipse", QIcon(":/icons/draw-ellipse.png")), "Dessiner &Cercle/Ellipse", self)
        self.circle_annot_action.setCheckable(True); self.circle_annot_action.triggered.connect(self.toggle_circle_annot_mode); self.circle_annot_action.setEnabled(False)
        self.line_annot_action = QAction(QIcon.fromTheme("draw-line", QIcon(":/icons/draw-line.png")), "Dessiner &Ligne", self)
        self.line_annot_action.setCheckable(True); self.line_annot_action.triggered.connect(self.toggle_line_annot_mode); self.line_annot_action.setEnabled(False)
        self.set_shape_border_color_action = QAction(QIcon.fromTheme("format-border-color", QIcon(":/icons/shape-border-color.png")), "Couleur Contour Formes...", self)
        self.set_shape_border_color_action.triggered.connect(self.set_shape_border_color); self.set_shape_border_color_action.setEnabled(False)
        self.set_shape_fill_color_action = QAction(QIcon.fromTheme("format-fill-color", QIcon(":/icons/shape-fill-color.png")), "Couleur Remplissage Formes...", self)
        self.set_shape_fill_color_action.triggered.connect(self.set_shape_fill_color); self.set_shape_fill_color_action.setEnabled(False)
        self.set_shape_border_width_action = QAction(QIcon.fromTheme("format-line-width", QIcon(":/icons/shape-border-width.png")), "Épaisseur Contour Formes...", self)
        self.set_shape_border_width_action.triggered.connect(self.set_shape_border_width); self.set_shape_border_width_action.setEnabled(False)
        self.text_annot_action = QAction(QIcon.fromTheme("mail-mark-unread", QIcon(":/icons/note-add.png")), "Ajouter une &Note Textuelle", self) 
        self.text_annot_action.setCheckable(True); self.text_annot_action.triggered.connect(self.toggle_text_annot_mode); self.text_annot_action.setEnabled(False)
        self.freetext_annot_action = QAction(QIcon.fromTheme("draw-text", QIcon(":/icons/draw-text.png")), "Ajouter &Zone de Texte", self)
        self.freetext_annot_action.setCheckable(True); self.freetext_annot_action.triggered.connect(self.toggle_freetext_annot_mode); self.freetext_annot_action.setEnabled(False)
        self.insert_image_action = QAction(QIcon.fromTheme("insert-image", QIcon(":/icons/insert-image.png")), "Ajouter &Image...", self)
        self.insert_image_action.setCheckable(True); self.insert_image_action.triggered.connect(self.toggle_insert_image_mode); self.insert_image_action.setEnabled(False)
        self.delete_selected_annot_action = QAction(QIcon.fromTheme("edit-clear", QIcon(":/icons/edit-clear.png")), "Supprimer Sélection", self) 
        self.delete_selected_annot_action.triggered.connect(self.delete_selected_item); self.delete_selected_annot_action.setEnabled(False)
        self.update_field_action = QAction("Mettre à jour Champ", self); self.update_field_action.triggered.connect(self.apply_widget_value_change); self.update_field_action.setEnabled(False)
        self.extract_text_page_action = QAction(QIcon.fromTheme("document-export", QIcon(":/icons/text-extract-page.png")), "Extraire Texte de la Page...", self)
        self.extract_text_page_action.triggered.connect(self.extract_text_current_page); self.extract_text_page_action.setEnabled(False)
        self.extract_text_doc_action = QAction(QIcon.fromTheme("document-export-table", QIcon(":/icons/text-extract-doc.png")), "Extraire Texte du Document...", self)
        self.extract_text_doc_action.triggered.connect(self.extract_text_entire_document); self.extract_text_doc_action.setEnabled(False)
        self.extract_images_doc_action = QAction(QIcon.fromTheme("image-x-generic", QIcon(":/icons/image-export.png")), "Extraire Images du Document...", self)
        self.extract_images_doc_action.triggered.connect(self.extract_images_from_document); self.extract_images_doc_action.setEnabled(False)
        self.merge_pdfs_action = QAction(QIcon.fromTheme("document-join", QIcon(":/icons/document-merge.png")), "&Fusionner des PDF...", self)
        self.merge_pdfs_action.setStatusTip("Fusionner plusieurs fichiers PDF en un seul")
        self.merge_pdfs_action.triggered.connect(self.merge_pdfs)
        # merge_pdfs_action est toujours active car elle ne dépend pas d'un doc ouvert

        self.split_pdf_each_page_action = QAction(QIcon.fromTheme("document-split", QIcon(":/icons/document-split-pages.png")), "Diviser Chaque Page...", self)
        self.split_pdf_each_page_action.setStatusTip("Diviser chaque page du PDF actuel en fichiers séparés")
        self.split_pdf_each_page_action.triggered.connect(self.split_pdf_each_page)
        self.split_pdf_each_page_action.setEnabled(False) # Activer quand un doc est ouvert

        self.split_pdf_by_range_action = QAction(QIcon.fromTheme("view-continuous", QIcon(":/icons/document-split-range.png")), "Diviser par Plage...", self)
        self.split_pdf_by_range_action.setStatusTip("Diviser le PDF actuel en plusieurs fichiers basés sur des plages de pages")
        self.split_pdf_by_range_action.triggered.connect(self.split_pdf_by_range)
        self.split_pdf_by_range_action.setEnabled(False) # Activer quand un doc est ouvert

        # Redaction Actions
        self.redaction_tool_action = QAction(QIcon.fromTheme("edit-redact", QIcon(":/icons/edit-redact.png")), "&Mode Rédaction", self) # Icon name might need adjustment
        self.redaction_tool_action.setCheckable(True)
        self.redaction_tool_action.setStatusTip("Activer le mode pour marquer les zones à rédiger")
        self.redaction_tool_action.triggered.connect(self.toggle_redaction_mode)
        self.redaction_tool_action.setEnabled(False)

        self.apply_redactions_action = QAction(QIcon.fromTheme("document-encrypt", QIcon(":/icons/apply-redactions.png")), "&Appliquer les Rédactions", self) # Icon name might need adjustment
        self.apply_redactions_action.setStatusTip("Appliquer les marques de rédaction sur la page actuelle pour supprimer définitivement le contenu")
        self.apply_redactions_action.triggered.connect(self.apply_redactions_on_current_page)
        self.apply_redactions_action.setEnabled(False)

        self.set_redaction_fill_color_action = QAction(QIcon.fromTheme("format-fill-color", QIcon(":/icons/redaction-fill-color.png")), "Couleur Remplissage Rédaction...", self)
        self.set_redaction_fill_color_action.setStatusTip("Choisir la couleur de remplissage pour les zones rédigées")
        self.set_redaction_fill_color_action.triggered.connect(self._set_redaction_fill_color) # Placeholder
        self.set_redaction_fill_color_action.setEnabled(False)

        self.set_redaction_overlay_text_action = QAction(QIcon.fromTheme("draw-text", QIcon(":/icons/redaction-overlay-text.png")), "Texte Superposé Rédaction...", self)
        self.set_redaction_overlay_text_action.setStatusTip("Définir un texte à superposer sur les zones rédigées")
        self.set_redaction_overlay_text_action.triggered.connect(self._set_redaction_overlay_text) # Placeholder
        self.set_redaction_overlay_text_action.setEnabled(False)


    def _create_menu_bar(self):
        # ... (Ajouter l'action de fusion au menu Outils ou Fichier)
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Fichier")
        file_menu.addAction(self.open_action); file_menu.addAction(self.save_action); file_menu.addAction(self.save_as_action)
        file_menu.addSeparator(); file_menu.addAction(self.exit_action)
        edit_menu = menu_bar.addMenu("&Édition")
        page_manip_submenu = edit_menu.addMenu("Manipulation de Pages")
        page_manip_submenu.addAction(self.delete_page_action); page_manip_submenu.addAction(self.insert_blank_page_action); page_manip_submenu.addAction(self.import_pages_action)
        page_manip_submenu.addSeparator(); page_manip_submenu.addAction(self.rotate_cw_action); page_manip_submenu.addAction(self.rotate_ccw_action); page_manip_submenu.addAction(self.crop_page_action)
        edit_menu.addSeparator()
        content_submenu = edit_menu.addMenu("Ajouter Contenu")
        content_submenu.addAction(self.freetext_annot_action); content_submenu.addAction(self.insert_image_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.delete_selected_annot_action); edit_menu.addAction(self.update_field_action) 
        annotation_menu = menu_bar.addMenu("&Annotation") 
        annotation_menu.addAction(self.highlight_action); annotation_menu.addAction(self.set_highlight_color_action); annotation_menu.addSeparator()
        annotation_menu.addAction(self.ink_action); annotation_menu.addAction(self.set_ink_color_action); annotation_menu.addAction(self.set_ink_thickness_action); annotation_menu.addSeparator()
        annotation_menu.addAction(self.rect_annot_action); annotation_menu.addAction(self.circle_annot_action); annotation_menu.addAction(self.line_annot_action)
        annotation_menu.addAction(self.set_shape_border_color_action); annotation_menu.addAction(self.set_shape_fill_color_action); annotation_menu.addAction(self.set_shape_border_width_action); annotation_menu.addSeparator()
        annotation_menu.addAction(self.text_annot_action) 
        view_menu = menu_bar.addMenu("&Vue")
        view_menu.addAction(self.zoom_in_action); view_menu.addAction(self.zoom_out_action); view_menu.addAction(self.zoom_original_action); view_menu.addSeparator()
        view_menu.addAction(self.page_thumbnails_dock.toggleViewAction()); view_menu.addAction(self.bookmarks_dock.toggleViewAction()); view_menu.addAction(self.properties_dock.toggleViewAction())
        form_menu = menu_bar.addMenu("Fo&rmulaires"); form_menu.addAction(self.update_field_action) 
        tools_menu = menu_bar.addMenu("&Outils")
        tools_menu.addAction(self.prev_page_action); tools_menu.addAction(self.next_page_action); tools_menu.addSeparator()
        extract_submenu = tools_menu.addMenu("Extraction"); extract_submenu.addAction(self.extract_text_page_action); extract_submenu.addAction(self.extract_text_doc_action); extract_submenu.addAction(self.extract_images_doc_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.merge_pdfs_action)
        split_submenu = tools_menu.addMenu("Division PDF")
        split_submenu.addAction(self.split_pdf_each_page_action)
        split_submenu.addAction(self.split_pdf_by_range_action)
        tools_menu.addSeparator()
        security_submenu = tools_menu.addMenu("&Sécurité") # Ou directement dans Outils
        security_submenu.addAction(self.redaction_tool_action)
        security_submenu.addAction(self.apply_redactions_action)
        security_submenu.addSeparator()
        security_submenu.addAction(self.set_redaction_fill_color_action)
        security_submenu.addAction(self.set_redaction_overlay_text_action)
        help_menu = menu_bar.addMenu("&Aide")

    def _create_tool_bars(self):
        # ... (Ajouter l'action à une barre d'outils "Document" ou similaire)
        file_tool_bar = self.addToolBar("Fichier"); file_tool_bar.setIconSize(QSize(24, 24)); file_tool_bar.addAction(self.open_action); file_tool_bar.addAction(self.save_action)
        navi_zoom_tool_bar = self.addToolBar("Navigation & Zoom"); navi_zoom_tool_bar.setIconSize(QSize(24,24))
        navi_zoom_tool_bar.addAction(self.prev_page_action); navi_zoom_tool_bar.addAction(self.next_page_action); navi_zoom_tool_bar.addSeparator()
        navi_zoom_tool_bar.addAction(self.zoom_out_action); navi_zoom_tool_bar.addAction(self.zoom_in_action); navi_zoom_tool_bar.addAction(self.zoom_original_action)
        page_manip_tool_bar = self.addToolBar("Manipulation de Page"); page_manip_tool_bar.setIconSize(QSize(24,24))
        page_manip_tool_bar.addAction(self.insert_blank_page_action); page_manip_tool_bar.addAction(self.import_pages_action); page_manip_tool_bar.addAction(self.delete_page_action); page_manip_tool_bar.addSeparator()
        page_manip_tool_bar.addAction(self.rotate_ccw_action); page_manip_tool_bar.addAction(self.rotate_cw_action); page_manip_tool_bar.addAction(self.crop_page_action)
        content_annot_tool_bar = self.addToolBar("Contenu & Annotation"); content_annot_tool_bar.setIconSize(QSize(24,24))
        content_annot_tool_bar.addAction(self.freetext_annot_action); content_annot_tool_bar.addAction(self.insert_image_action); content_annot_tool_bar.addSeparator()
        content_annot_tool_bar.addAction(self.highlight_action); content_annot_tool_bar.addAction(self.set_highlight_color_action); content_annot_tool_bar.addSeparator()
        content_annot_tool_bar.addAction(self.ink_action); content_annot_tool_bar.addAction(self.set_ink_color_action); content_annot_tool_bar.addAction(self.set_ink_thickness_action); content_annot_tool_bar.addSeparator()
        content_annot_tool_bar.addAction(self.rect_annot_action); content_annot_tool_bar.addAction(self.circle_annot_action); content_annot_tool_bar.addAction(self.line_annot_action)
        content_annot_tool_bar.addAction(self.set_shape_border_color_action); content_annot_tool_bar.addAction(self.set_shape_fill_color_action); content_annot_tool_bar.addAction(self.set_shape_border_width_action); content_annot_tool_bar.addSeparator()
        content_annot_tool_bar.addAction(self.text_annot_action); content_annot_tool_bar.addSeparator(); content_annot_tool_bar.addAction(self.delete_selected_annot_action) 
        form_tool_bar = self.addToolBar("Formulaires"); form_tool_bar.addAction(self.update_field_action)
        extract_tool_bar = self.addToolBar("Extraction"); extract_tool_bar.addAction(self.extract_text_page_action); extract_tool_bar.addAction(self.extract_text_doc_action); extract_tool_bar.addAction(self.extract_images_doc_action)
        
        doc_tools_bar = self.addToolBar("Outils Document") # Nouvelle barre ou existante
        doc_tools_bar.addAction(self.merge_pdfs_action)
        doc_tools_bar.addAction(self.split_pdf_each_page_action)
        doc_tools_bar.addAction(self.split_pdf_by_range_action)

        security_tool_bar = self.addToolBar("Sécurité")
        security_tool_bar.setIconSize(QSize(24,24))
        security_tool_bar.addAction(self.redaction_tool_action)
        security_tool_bar.addAction(self.apply_redactions_action)
        security_tool_bar.addSeparator()
        security_tool_bar.addAction(self.set_redaction_fill_color_action)
        security_tool_bar.addAction(self.set_redaction_overlay_text_action)


    def _setup_central_widget(self): # ... (inchangé)
        self.pdf_view = QGraphicsView(self); self.pdf_scene = QGraphicsScene(self); self.pdf_view.setScene(self.pdf_scene)
        self.pdf_view_item = QGraphicsPixmapItem(); self.pdf_scene.addItem(self.pdf_view_item)
        self.pdf_view.mousePressEvent = self.graphics_view_mouse_press; self.pdf_view.mouseMoveEvent = self.graphics_view_mouse_move; self.pdf_view.mouseReleaseEvent = self.graphics_view_mouse_release
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setWidget(self.pdf_view); self.setCentralWidget(scroll_area)
    def _create_dock_widgets(self): # ... (inchangé)
        self.page_thumbnails_dock = QDockWidget("Miniatures", self); self.page_thumbnails_list = QListWidget(); self.page_thumbnails_list.itemClicked.connect(self.go_to_page_from_thumbnail)
        self.page_thumbnails_list.setDragEnabled(True); self.page_thumbnails_list.setAcceptDrops(True); self.page_thumbnails_list.setDropIndicatorShown(True); self.page_thumbnails_list.setDefaultDropAction(Qt.MoveAction)
        self.page_thumbnails_list.model().rowsMoved.connect(self.on_thumbnail_rows_moved); self.page_thumbnails_dock.setWidget(self.page_thumbnails_list); self.addDockWidget(Qt.LeftDockWidgetArea, self.page_thumbnails_dock)
        
        self.bookmarks_dock = QDockWidget("Signets", self)
        self.bookmarks_tree = QTreeWidget() # Changed from QListWidget
        self.bookmarks_tree.setHeaderLabels(["Titre"]) # Set header label
        self.bookmarks_tree.itemClicked.connect(self._on_bookmark_clicked) # Connect signal
        self.bookmarks_dock.setWidget(self.bookmarks_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bookmarks_dock)
        
        self.tabifyDockWidget(self.page_thumbnails_dock, self.bookmarks_dock)
        self.properties_dock = QDockWidget("Propriétés", self); self.properties_widget_container = QWidget(); self.property_widget_layout = QVBoxLayout(self.properties_widget_container)
        self.property_widget_layout.setAlignment(Qt.AlignTop); self.properties_label_info = QLabel("Aucun élément."); self.property_widget_layout.addWidget(self.properties_label_info)
        self.properties_dock.setWidget(self.properties_widget_container); self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
    def _create_navigation_bar(self): # ... (inchangé)
        nav_widget = QWidget(); nav_layout = QHBoxLayout(nav_widget)
        self.prev_page_button = QPushButton(QIcon.fromTheme("go-previous"), "<"); self.prev_page_button.clicked.connect(self.go_to_previous_page); self.prev_page_button.setEnabled(False)
        self.page_spinbox = QSpinBox(); self.page_spinbox.setMinimum(1); self.page_spinbox.setEnabled(False); self.page_spinbox.valueChanged.connect(self.go_to_page_from_spinbox)
        self.total_pages_label = QLabel("/ N/A"); self.next_page_button = QPushButton(QIcon.fromTheme("go-next"), ">"); self.next_page_button.clicked.connect(self.go_to_next_page); self.next_page_button.setEnabled(False)
        nav_layout.addStretch(); nav_layout.addWidget(self.prev_page_button); nav_layout.addWidget(self.page_spinbox); nav_layout.addWidget(self.total_pages_label); nav_layout.addWidget(self.next_page_button); nav_layout.addStretch()
        navigation_toolbar = QToolBar("Navigation"); navigation_toolbar.setMovable(False); navigation_toolbar.addWidget(nav_widget); self.addToolBar(Qt.BottomToolBarArea, navigation_toolbar)
    def _clear_property_widgets(self): # ... (inchangé)
        for widget in self.current_prop_widgets: self.property_widget_layout.removeWidget(widget); widget.deleteLater()
        self.current_prop_widgets = [] 
        if self.property_widget_layout.count() == 0 or self.property_widget_layout.itemAt(0).widget() != self.properties_label_info :
            if self.properties_label_info.parentWidget() is None: self.property_widget_layout.insertWidget(0, self.properties_label_info)
            else: self.properties_label_info.raise_()
        self.properties_label_info.setText("Aucun élément sélectionné.")
        self.update_field_action.setEnabled(False)
        
    def _reset_ui_on_error(self): 
        self.pdf_scene.clear(); self.pdf_view_item = QGraphicsPixmapItem(); self.pdf_scene.addItem(self.pdf_view_item); self.pdf_view_item.setPixmap(QPixmap())
        self.setWindowTitle("Éditeur PDF PyQt"); 
        self.page_thumbnails_list.clear()
        self.bookmarks_tree.clear() 
        self._clear_pending_redactions() # Clear pending redaction marks
        self.update_navigation_controls() 
        actions_to_disable = [
            self.save_action, self.save_as_action, self.zoom_in_action, self.zoom_out_action, self.zoom_original_action,
            self.delete_page_action, self.insert_blank_page_action, self.import_pages_action, self.rotate_cw_action,
            self.rotate_ccw_action, self.crop_page_action, self.highlight_action, self.set_highlight_color_action,
            self.ink_action, self.set_ink_color_action, self.set_ink_thickness_action, self.rect_annot_action,
            self.circle_annot_action, self.line_annot_action, self.set_shape_border_color_action,
            self.set_shape_fill_color_action, self.set_shape_border_width_action, self.text_annot_action,
            self.freetext_annot_action, self.insert_image_action, self.delete_selected_annot_action, 
            self.update_field_action, self.extract_text_page_action, self.extract_text_doc_action,
            self.extract_images_doc_action, self.split_pdf_each_page_action, self.split_pdf_by_range_action,
            self.redaction_tool_action, self.apply_redactions_action,
            self.set_redaction_fill_color_action, self.set_redaction_overlay_text_action
            # self.merge_pdfs_action # Ne dépend pas d'un doc ouvert
        ]
        for action in actions_to_disable:
            action.setEnabled(False)
            if hasattr(action, 'isCheckable') and action.isCheckable(): action.setChecked(False)
        self._clear_selected_item_feedback(); self.current_tool_mode = "pointer"; self.statusBar().showMessage("Erreur. Prêt.")
        
    def open_file(self): 
        if not self._ask_save_before_action(): return 
        if self.current_pdf_document:
            try: self.current_pdf_document.close()
            except Exception as e: logging.warning(f"Erreur fermeture: {e}")
            self.current_pdf_document = None
            # _reset_ui_on_error() also clears thumbnails, bookmarks, and pending redactions
            self._reset_ui_on_error() 
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir PDF", "", "Fichiers PDF (*.pdf)")
        if file_path:
            try:
                self.current_pdf_document = fitz.open(file_path); self.current_page_number = 0; self.current_zoom_factor = 1.0; self.is_document_modified = False 
                self.update_page_view(); self.update_thumbnails(); self.update_navigation_controls()
                actions_to_enable = [
                    self.save_action, self.save_as_action, self.zoom_in_action, self.zoom_out_action, self.zoom_original_action,
                    self.delete_page_action, self.insert_blank_page_action, self.import_pages_action, self.rotate_cw_action,
                    self.rotate_ccw_action, self.crop_page_action, self.highlight_action, self.set_highlight_color_action,
                    self.ink_action, self.set_ink_color_action, self.set_ink_thickness_action, self.rect_annot_action,
                    self.circle_annot_action, self.line_annot_action, self.set_shape_border_color_action,
                    self.set_shape_fill_color_action, self.set_shape_border_width_action, self.text_annot_action,
                    self.freetext_annot_action, self.insert_image_action, 
                    self.extract_text_page_action, self.extract_text_doc_action, self.extract_images_doc_action,
                    self.split_pdf_each_page_action, self.split_pdf_by_range_action,
                    self.redaction_tool_action, # Apply redactions will be enabled when marks are made
                    self.set_redaction_fill_color_action, self.set_redaction_overlay_text_action
                ]
                for action in actions_to_enable: action.setEnabled(True)
                # self.merge_pdfs_action.setEnabled(True) # Toujours active
                self.statusBar().showMessage(f"Ouvert : {file_path}"); logging.info(f"PDF ouvert : {file_path}")
                self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1}/{self.current_pdf_document.page_count} [{file_path}]")
                self._load_bookmarks() # Load bookmarks after opening file
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Ouverture impossible '{file_path}'.\nErreur : {e}"); self.current_pdf_document = None; self._reset_ui_on_error()

    def _load_bookmarks(self):
        self.bookmarks_tree.clear()
        if not self.current_pdf_document:
            return

        toc = self.current_pdf_document.get_toc(simple=False)
        if not toc:
            return

        def add_items_recursively(parent_item, toc_list, current_level_toc_entries):
            for i, entry in enumerate(current_level_toc_entries):
                level, title, page_num, dest_dict = entry
                item = QTreeWidgetItem([title])
                item.setData(0, Qt.UserRole, {'page': page_num - 1, 'dest_details': dest_dict})
                parent_item.addChild(item)
                
                children_toc_entries = []
                start_search_idx = toc_list.index(entry) + 1 
                for k in range(start_search_idx, len(toc_list)):
                    next_entry = toc_list[k]
                    next_level = next_entry[0]
                    if next_level == level + 1:
                        children_toc_entries.append(next_entry)
                    elif next_level <= level: 
                        break
                if children_toc_entries:
                    add_items_recursively(item, toc_list, children_toc_entries)
        
        top_level_items = [entry for entry in toc if entry[0] == 1]
        add_items_recursively(self.bookmarks_tree, toc, top_level_items)
        self.bookmarks_tree.expandAll() 

    def _on_bookmark_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not (data and isinstance(data, dict) and 'page' in data):
            logging.warning(f"Bookmark click: No valid page data found for item: {item.text(0)}")
            return

        page_num_0_indexed = data['page']
        dest_details = data.get('dest_details', {})
        
        if not (self.current_pdf_document and 0 <= page_num_0_indexed < self.current_pdf_document.page_count):
            logging.warning(f"Bookmark click: Invalid page number {page_num_0_indexed} or no document. Data: {data}")
            return
            
        logging.info(f"Bookmark clicked: Navigating to page {page_num_0_indexed + 1}. Details: {dest_details}")
        
        self.go_to_page(page_num_0_indexed)

        def _apply_specific_destination_details():
            if not self.current_pdf_document or self.current_page_number != page_num_0_indexed:
                logging.info("Page context changed before specific destination could be applied for bookmark.")
                return

            logging.debug(f"Attempting to apply specific destination for page {self.current_page_number +1}: {dest_details}")
            
            new_zoom = dest_details.get('zoom', 0)
            zoom_changed = False
            if new_zoom > 0 and abs(self.current_zoom_factor - new_zoom) > 0.01:
                logging.debug(f"Bookmark zoom: Setting zoom to: {new_zoom}")
                self.set_zoom_factor(new_zoom) 
                zoom_changed = True

            if zoom_changed:
                QTimer.singleShot(0, lambda: self._scroll_to_destination_point(dest_details, page_num_0_indexed))
            else:
                self._scroll_to_destination_point(dest_details, page_num_0_indexed)

        QTimer.singleShot(0, _apply_specific_destination_details)

    def _scroll_to_destination_point(self, dest_details: dict, target_page_num_0_indexed: int):
        if not self.current_pdf_document or self.current_page_number != target_page_num_0_indexed:
            logging.warning(f"Scroll attempt aborted: page context changed (current: {self.current_page_number}, target: {target_page_num_0_indexed}).")
            return

        to_point_data = dest_details.get('to') 
        scroll_area = self.centralWidget() 
        
        if not (scroll_area and isinstance(scroll_area, QScrollArea)):
            logging.warning("Could not find QScrollArea to adjust scrollbars for bookmark destination.")
            return

        if to_point_data and isinstance(to_point_data, fitz.Point):
            scene_x = to_point_data.x * self.current_zoom_factor
            scene_y = to_point_data.y * self.current_zoom_factor
            logging.debug(f"Scrolling to PDF point {to_point_data}, scene point ({scene_x}, {scene_y}) at zoom {self.current_zoom_factor}")
            scroll_area.horizontalScrollBar().setValue(int(scene_x))
            scroll_area.verticalScrollBar().setValue(int(scene_y))
        elif dest_details.get('top') is not None: 
            pdf_y = dest_details.get('top', 0.0) 
            should_scroll_y = False
            if pdf_y > 0: 
                should_scroll_y = True
            elif dest_details.get('zoom', -1) == 0 and (not to_point_data or to_point_data.y == 0) and pdf_y == 0:
                if dest_details.get('left', -1) != 0 : 
                     should_scroll_y = True 

            if should_scroll_y:
                scene_y = pdf_y * self.current_zoom_factor
                logging.debug(f"Scrolling to Y-pos based on 'top' heuristic: PDF Y={pdf_y}, Scene Y={scene_y} at zoom {self.current_zoom_factor}")
                scroll_area.verticalScrollBar().setValue(int(scene_y))
        
    def apply_redactions_on_current_page(self):
        # This will be implemented in a later step
        QMessageBox.information(self, "Info", "Apply redactions functionality to be implemented.")
        pass


    # ... (Autres méthodes jusqu'à extract_images_from_document)
    def update_page_view(self):
        if not self.current_pdf_document or self.current_page_number < 0 or self.current_page_number >= self.current_pdf_document.page_count:
            if self.current_pdf_document and self.current_pdf_document.page_count == 0 : 
                self._clear_selected_item_feedback(); self.pdf_scene.clear(); self.pdf_view_item = QGraphicsPixmapItem(); self.pdf_scene.addItem(self.pdf_view_item); self.pdf_view_item.setPixmap(QPixmap())
                self.setWindowTitle("Éditeur PDF PyQt - Document Vide"); self.update_navigation_controls() 
            else: self._reset_ui_on_error() # This also calls _clear_pending_redactions
            return
        
        self._clear_pending_redactions() # Clear marks when page view updates (e.g. page change, zoom)

        try: page = self.current_pdf_document.load_page(self.current_page_number)
        except Exception as e: self._reset_ui_on_error(); return # This also calls _clear_pending_redactions
        matrix = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor); pix = page.get_pixmap(matrix=matrix)
        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage); self._clear_selected_item_feedback() 
        self.pdf_scene.clear(); self.pdf_view_item = QGraphicsPixmapItem(pixmap); self.pdf_scene.addItem(self.pdf_view_item)
        self.pdf_scene.setSceneRect(QRectF(pixmap.rect())) 
        doc_name = self.current_pdf_document.name if hasattr(self.current_pdf_document, 'name') and self.current_pdf_document.name else "Nouveau Document"
        self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1}/{self.current_pdf_document.page_count} [{doc_name}]")
        self.update_navigation_controls()

    def update_thumbnails(self): 
        self.page_thumbnails_list.clear()
        if self.current_pdf_document:
            for i in range(self.current_pdf_document.page_count):
                page = self.current_pdf_document.load_page(i); thumb_matrix = fitz.Matrix(0.2, 0.2) ; pix = page.get_pixmap(matrix=thumb_matrix)
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888)
                item = QListWidgetItem(QIcon(QPixmap.fromImage(qimage)), f"Page {i + 1}"); self.page_thumbnails_list.addItem(item)
            if self.current_pdf_document.page_count > 0 and self.current_page_number >=0 : self.page_thumbnails_list.setCurrentRow(self.current_page_number)

    def update_navigation_controls(self): 
        if self.current_pdf_document and self.current_pdf_document.page_count > 0:
            num_pages = self.current_pdf_document.page_count
            self.prev_page_action.setEnabled(self.current_page_number > 0); self.next_page_action.setEnabled(self.current_page_number < num_pages - 1)
            self.prev_page_button.setEnabled(self.current_page_number > 0); self.next_page_button.setEnabled(self.current_page_number < num_pages - 1)
            self.page_spinbox.setEnabled(True); self.page_spinbox.blockSignals(True) 
            self.page_spinbox.setRange(1, num_pages); self.page_spinbox.setValue(self.current_page_number + 1); self.page_spinbox.blockSignals(False) 
            self.total_pages_label.setText(f"/ {num_pages}")
        else: 
            self.prev_page_action.setEnabled(False); self.next_page_action.setEnabled(False); self.prev_page_button.setEnabled(False); self.next_page_button.setEnabled(False)
            self.page_spinbox.setEnabled(False); self.page_spinbox.setRange(0,0); self.page_spinbox.setValue(0); self.total_pages_label.setText("/ 0")

    def go_to_page(self, page_num): 
        if self.current_pdf_document and 0 <= page_num < self.current_pdf_document.page_count:
            # Only update if page actually changes, or if the view is currently empty
            if self.current_page_number != page_num or not self.pdf_view_item.pixmap() or self.pdf_view_item.pixmap().isNull():
                self.current_page_number = page_num
                self.update_page_view() # This will also clear pending redactions for the new page
                self.page_thumbnails_list.setCurrentRow(self.current_page_number)
            # If it's the same page and already rendered, do nothing to avoid redundant updates / clearing redaction marks
            # unless explicitly desired by other operations.

    def go_to_previous_page(self): self.go_to_page(self.current_page_number - 1)
    def go_to_next_page(self): self.go_to_page(self.current_page_number + 1)
    def go_to_page_from_thumbnail(self, item): self.go_to_page(self.page_thumbnails_list.row(item))
    def go_to_page_from_spinbox(self, value): self.go_to_page(value - 1)
    def zoom(self, factor): 
        new_zoom = self.current_zoom_factor * factor
        # Add some clamping if desired, e.g., self.current_zoom_factor = max(0.1, min(new_zoom, 10.0))
        self.current_zoom_factor = new_zoom
        self.update_page_view(); # This will also clear pending redactions
        self.zoom_original_action.setEnabled(abs(self.current_zoom_factor - 1.0) > 0.01)

    def set_zoom_factor(self, factor): 
        self.current_zoom_factor = factor
        self.update_page_view(); # This will also clear pending redactions
        self.zoom_original_action.setEnabled(abs(self.current_zoom_factor - 1.0) > 0.01)

    def save_file(self): 
        if not self.current_pdf_document: return
        file_path_to_save = self.current_pdf_document.name if hasattr(self.current_pdf_document, 'name') and self.current_pdf_document.name else ""
        if not file_path_to_save: self.save_file_as(); return
        try: 
            # Before saving, ensure any temporary scene items (like selection_rect_item) are removed
            if self.selection_rect_item and self.selection_rect_item.scene():
                 self.pdf_scene.removeItem(self.selection_rect_item)
                 self.selection_rect_item = None

            self.current_pdf_document.save(file_path_to_save, garbage=3, deflate=True); 
            self.statusBar().showMessage(f"Fichier sauvegardé : {file_path_to_save}"); 
            self.is_document_modified = False 
        except Exception as e: QMessageBox.critical(self, "Erreur sauvegarde", f"Erreur : {e}")

    def save_file_as(self): 
        if not self.current_pdf_document: QMessageBox.warning(self, "Aucun document", "Aucun document ouvert."); return
        current_path = self.current_pdf_document.name if hasattr(self.current_pdf_document, 'name') and self.current_pdf_document.name else ""
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer PDF sous...", current_path, "Fichiers PDF (*.pdf)")
        if file_path:
            try: 
                if self.selection_rect_item and self.selection_rect_item.scene(): # Clear temp item
                    self.pdf_scene.removeItem(self.selection_rect_item)
                    self.selection_rect_item = None

                self.current_pdf_document.save(file_path, garbage=3, deflate=True); 
                self.statusBar().showMessage(f"Sauvegardé sous : {file_path}")
                original_page_number = self.current_page_number; 
                self.current_pdf_document.close(); 
                self.current_pdf_document = fitz.open(file_path) # Re-open the saved document
                self.current_page_number = original_page_number 
                if self.current_page_number >= self.current_pdf_document.page_count: 
                    self.current_page_number = max(0, self.current_pdf_document.page_count -1)
                self.update_page_view(); self.update_thumbnails(); self.update_navigation_controls(); 
                self.is_document_modified = False
            except Exception as e: QMessageBox.critical(self, "Erreur sauvegarde", f"Erreur : {e}")

    def _ask_save_before_action(self): 
        if not self.is_document_modified or not self.current_pdf_document: return True
        user_choice = QMessageBox.question(self, "Modifications non sauvegardées", "Sauvegarder les modifications ?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel) 
        if user_choice == QMessageBox.Save: self.save_file(); return not self.is_document_modified 
        return user_choice == QMessageBox.Discard

    def closeEvent(self, event): 
        if self._ask_save_before_action():
            if self.current_pdf_document: 
                try: self.current_pdf_document.close()
                except Exception as e: logging.warning(f"Erreur fermeture doc: {e}")
            super().closeEvent(event)
        else: event.ignore()

    def on_thumbnail_rows_moved(self, parent, start_row, end_row, destination_parent, destination_row): 
        if not self.current_pdf_document: return
        if (end_row - start_row + 1) == 1: # Only single item drag is properly handled for now
            moved_idx, new_idx = start_row, destination_row
            if new_idx > moved_idx: new_idx -= 1 
            if moved_idx == new_idx: return
            try:
                current_page_xref = self.current_pdf_document[self.current_page_number].xref
                self.current_pdf_document.move_page(moved_idx, new_idx)
                self.is_document_modified = True
                self.update_thumbnails() # Rebuild thumbnails in new order
                
                # Try to find the previously current page by its xref to update current_page_number
                new_current_page_idx = -1
                for i, page_obj in enumerate(self.current_pdf_document):
                    if page_obj.xref == current_page_xref:
                        new_current_page_idx = i
                        break
                
                if new_current_page_idx != -1:
                    self.current_page_number = new_current_page_idx
                elif self.current_pdf_document.page_count > 0: # Fallback if xref not found (should not happen)
                    self.current_page_number = min(max(0, moved_idx), self.current_pdf_document.page_count -1)
                else: # No pages left
                    self.current_page_number = -1

                if self.current_pdf_document.page_count == 0: 
                    self._reset_ui_on_error()
                else: 
                    self.update_navigation_controls()
                    self.page_thumbnails_list.setCurrentRow(self.current_page_number) # Highlight moved page if it was current
                    self.go_to_page(self.current_page_number) # Ensure view updates if current page index changed due to move
                
                doc_name = self.current_pdf_document.name or "Nouveau Document"
                self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1 if self.current_page_number >=0 else 'N/A'}/{self.current_pdf_document.page_count} [{doc_name}]")
                self.statusBar().showMessage("Ordre des pages modifié.")
            except Exception as e: 
                QMessageBox.critical(self, "Erreur réorganisation", f"Erreur: {e}")
                self.update_thumbnails() # Refresh to original state on error
        else: 
            self.update_thumbnails() # Multi-item drag not supported, refresh
            QMessageBox.information(self, "Fonctionnalité Limitée", "Le déplacement de plusieurs miniatures à la fois n'est pas encore pleinement supporté.")

    def delete_current_page(self): 
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0: return
        idx_to_delete = self.current_page_number
        num_pages_before_delete = self.current_pdf_document.page_count

        msg = f"Supprimer la page {idx_to_delete + 1} sur {num_pages_before_delete} ?"
        if num_pages_before_delete == 1:
            msg = "Supprimer la dernière page du document ?"
        
        if QMessageBox.question(self, "Confirmation de Suppression", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No: 
            return
        try:
            self.current_pdf_document.delete_page(idx_to_delete)
            self.is_document_modified = True
            self.statusBar().showMessage(f"Page {idx_to_delete + 1} supprimée.")
            
            if self.current_pdf_document.page_count == 0: 
                self.current_page_number = -1
                self._reset_ui_on_error() # Resets UI, disables page-specific actions
                self.delete_page_action.setEnabled(False) # Explicitly disable delete action
            else: 
                # Adjust current page number if necessary
                self.current_page_number = min(idx_to_delete, self.current_pdf_document.page_count - 1)
                self.update_page_view() # This will also clear pending redactions
                self.update_thumbnails()
                self.update_navigation_controls()
            self.save_action.setEnabled(True)
        except Exception as e: 
            QMessageBox.critical(self, "Erreur de Suppression", f"Erreur: {e}")
            self.update_thumbnails() # Refresh in case of error

    def insert_blank_page(self): 
        if not self.current_pdf_document: 
            QMessageBox.warning(self, "Aucun Document", "Ouvrez ou créez un document pour insérer une page.")
            return
        
        insert_at_idx = self.current_page_number + 1 # Default insert after current
        if self.current_pdf_document.page_count == 0: # If document is empty
            insert_at_idx = 0
        
        page_width, page_height = fitz.paper_size("a4") # Default to A4
        if self.current_pdf_document.page_count > 0 and self.current_page_number != -1 :
            try:
                current_page_rect = self.current_pdf_document[self.current_page_number].rect
                page_width, page_height = current_page_rect.width, current_page_rect.height
            except Exception as e:
                logging.warning(f"Could not get current page size, defaulting to A4. Error: {e}")
        
        msg = f"Insérer une page vierge à la position {insert_at_idx + 1} (taille: {int(page_width)}x{int(page_height)})?"
        if QMessageBox.question(self, "Insérer Page Vierge", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.No:
            return
        try:
            self.current_pdf_document.new_page(pno=insert_at_idx, width=page_width, height=page_height)
            self.is_document_modified = True
            self.statusBar().showMessage(f"Page vierge insérée à la position {insert_at_idx + 1}.")
            self.current_page_number = insert_at_idx # Go to the new page
            
            self.update_page_view() # This will also clear pending redactions
            self.update_thumbnails()
            self.update_navigation_controls()
            self.delete_page_action.setEnabled(True) # Enable if it was disabled (e.g. for empty doc)
            self.save_action.setEnabled(True)
        except Exception as e: 
            QMessageBox.critical(self, "Erreur d'Insertion", f"Erreur: {e}")
            self.update_thumbnails()

    def import_pages_from_pdf(self): 
        if not self.current_pdf_document: 
            QMessageBox.warning(self, "Aucun Document", "Ouvrez ou créez un document cible d'abord.")
            return

        src_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner le PDF source à importer", "", "Fichiers PDF (*.pdf)")
        if not src_path: 
            return
        
        try:
            src_doc = fitz.open(src_path)
            if src_doc.page_count == 0:
                QMessageBox.information(self, "PDF Source Vide", "Le document PDF source sélectionné est vide.")
                src_doc.close()
                return

            # For simplicity, always append. Could add dialog for choosing insertion point.
            insert_at_idx = self.current_pdf_document.page_count 
            
            self.current_pdf_document.insert_pdf(src_doc) # Appends all pages from src_doc
            self.is_document_modified = True
            src_doc.close()
            
            self.statusBar().showMessage(f"{src_doc.page_count} page(s) importée(s) à la fin du document.")
            self.current_page_number = insert_at_idx # Go to the first imported page
            
            self.update_page_view()
            self.update_thumbnails()
            self.update_navigation_controls()
            self.save_action.setEnabled(True)
            if self.current_pdf_document.page_count > 0:
                self.delete_page_action.setEnabled(True)

        except Exception as e: 
            QMessageBox.critical(self, "Erreur d'Importation", f"Erreur lors de l'importation des pages: {e}")
            if 'src_doc' in locals() and src_doc.is_open: 
                src_doc.close()
            self.update_thumbnails() # Refresh thumbnails in case of partial success or error

    def rotate_current_page(self, angle): 
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0 or self.current_page_number < 0 : return
        try: 
            page = self.current_pdf_document[self.current_page_number]
            page.set_rotation((page.rotation + angle) % 360)
            self.is_document_modified = True
            self.statusBar().showMessage(f"Page {self.current_page_number + 1} pivotée de {angle} degrés.")
            self._refresh_page_and_thumbnail() # This calls update_page_view which clears pending redactions
        except Exception as e: QMessageBox.critical(self, "Erreur de Rotation", f"Erreur: {e}")

    def crop_current_page(self): 
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0 or self.current_page_number < 0: return
        
        page_index = self.current_page_number
        page = self.current_pdf_document.load_page(page_index)
        original_mediabox = page.rect # This is the MediaBox
        current_cropbox = page.cropbox if page.cropbox else original_mediabox # Fallback to MediaBox if CropBox not set

        # Present current cropbox, allow user to input new one relative to MediaBox
        # Coords are (x0, y0, x1, y1)
        cropbox_str = f"{current_cropbox.x0:.2f} {current_cropbox.y0:.2f} {current_cropbox.x1:.2f} {current_cropbox.y1:.2f}"
        prompt_text = (f"Page {page_index + 1} - Définir le CropBox (x0 y0 x1 y1).\n"
                       f"CropBox Actuel: {cropbox_str}\n"
                       f"MediaBox (limites): {original_mediabox.x0:.2f} {original_mediabox.y0:.2f} {original_mediabox.x1:.2f} {original_mediabox.y1:.2f}\n"
                       "Entrez les nouvelles coordonnées du CropBox:")
        
        new_cropbox_str, ok = QInputDialog.getText(self, "Rogner la Page", prompt_text, QLineEdit.Normal, cropbox_str)
        
        if ok and new_cropbox_str:
            try:
                coords = list(map(float, new_cropbox_str.split()))
                if len(coords) != 4:
                    raise ValueError("Quatre coordonnées sont requises (x0 y0 x1 y1).")
                
                new_cropbox_rect = fitz.Rect(coords[0], coords[1], coords[2], coords[3]).normalize()

                # Validate new_cropbox: must be valid, not empty, and within MediaBox
                if not new_cropbox_rect.is_valid or new_cropbox_rect.is_empty:
                    QMessageBox.warning(self, "CropBox Invalide", "Les coordonnées du CropBox forment un rectangle invalide ou vide.")
                    return
                
                # CropBox should ideally be contained within or equal to MediaBox.
                # However, PDF spec allows it to be outside, but viewers might clip to MediaBox.
                # For simplicity, let's allow it as long as it's valid. User should be aware of MediaBox.
                # A stricter check: if not original_mediabox.contains(new_cropbox_rect):
                #    QMessageBox.warning(self, "CropBox Invalide", "Le CropBox doit être contenu dans le MediaBox de la page.")
                #    return

                page.set_cropbox(new_cropbox_rect)
                self.is_document_modified = True
                self.statusBar().showMessage(f"Page {page_index + 1} rognée (CropBox modifié).")
                self._refresh_page_and_thumbnail() # This calls update_page_view which clears pending redactions
            except ValueError as ve:
                QMessageBox.critical(self, "Erreur de Format", f"Format des coordonnées invalide: {ve}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur de Rognage", f"Une erreur est survenue lors du rognage: {e}")

    # --- Gestion des outils d'annotation ---
    def toggle_highlight_mode(self, checked): 
        if checked: self.current_tool_mode = "highlight"; self._update_tool_mode_ui("Surlignage"); self._deselect_all_tool_actions_but_one(self.highlight_action)
        elif self.current_tool_mode == "highlight": self._update_tool_mode_ui(None)
    def toggle_ink_mode(self, checked): 
        if checked: self.current_tool_mode = "ink"; self._update_tool_mode_ui("Dessin (Stylo)"); self._deselect_all_tool_actions_but_one(self.ink_action)
        elif self.current_tool_mode == "ink": self._update_tool_mode_ui(None)
    def toggle_rect_annot_mode(self, checked): 
        if checked: self.current_tool_mode = "rect_annot"; self._update_tool_mode_ui("Dessin Rectangle"); self._deselect_all_tool_actions_but_one(self.rect_annot_action)
        elif self.current_tool_mode == "rect_annot": self._update_tool_mode_ui(None)
    def toggle_circle_annot_mode(self, checked): 
        if checked: self.current_tool_mode = "circle_annot"; self._update_tool_mode_ui("Dessin Cercle/Ellipse"); self._deselect_all_tool_actions_but_one(self.circle_annot_action)
        elif self.current_tool_mode == "circle_annot": self._update_tool_mode_ui(None)
    def toggle_line_annot_mode(self, checked): 
        if checked: self.current_tool_mode = "line_annot"; self._update_tool_mode_ui("Dessin Ligne"); self._deselect_all_tool_actions_but_one(self.line_annot_action)
        elif self.current_tool_mode == "line_annot": self._update_tool_mode_ui(None)
    def toggle_text_annot_mode(self, checked): 
        if checked: self.current_tool_mode = "text_annot"; self._update_tool_mode_ui("Ajout de Note Textuelle"); self._deselect_all_tool_actions_but_one(self.text_annot_action)
        elif self.current_tool_mode == "text_annot": self._update_tool_mode_ui(None)
    def toggle_freetext_annot_mode(self, checked): 
        if checked: self.current_tool_mode = "freetext_annot"; self._update_tool_mode_ui("Ajout Zone de Texte"); self._deselect_all_tool_actions_but_one(self.freetext_annot_action)
        elif self.current_tool_mode == "freetext_annot": self._update_tool_mode_ui(None)
    def toggle_insert_image_mode(self, checked): 
        if checked: self.current_tool_mode = "insert_image"; self._update_tool_mode_ui("Insertion d'Image"); self._deselect_all_tool_actions_but_one(self.insert_image_action)
        elif self.current_tool_mode == "insert_image" and not checked: self._update_tool_mode_ui(None) 


    def toggle_redaction_mode(self, checked):
        if checked:
            self.current_tool_mode = "redaction"
            self._update_tool_mode_ui("Rédaction")
            self._deselect_all_tool_actions_but_one(self.redaction_tool_action)
            # self.apply_redactions_action state depends on self.pending_redactions
        elif self.current_tool_mode == "redaction": 
            self._update_tool_mode_ui(None) # This will call _clear_pending_redactions


    def _deselect_all_tool_actions_but_one(self, current_action: QAction): 
        tool_actions = [ 
            self.highlight_action, self.ink_action, 
            self.rect_annot_action, self.circle_annot_action, self.line_annot_action, 
            self.text_annot_action, self.freetext_annot_action, self.insert_image_action,
            self.redaction_tool_action
        ]
        for action in tool_actions:
            if action != current_action: action.setChecked(False)
    
    def _update_tool_mode_ui(self, mode_name=None): 
        if mode_name:
            logging.debug(f"Mode {mode_name} activé."); self.statusBar().showMessage(f"Mode {mode_name} Activé.")
            cursor_shape = Qt.CrossCursor 
            if mode_name == "text_annot": cursor_shape = Qt.PointingHandCursor
            elif mode_name == "pointer": cursor_shape = Qt.ArrowCursor
            
            self.pdf_view.setCursor(cursor_shape)
            self._clear_selected_item_feedback()
            
            # If switching to a mode that is NOT redaction, and current mode WAS redaction, clear pending.
            if self.current_tool_mode == "redaction" and mode_name != "Rédaction":
                self._clear_pending_redactions()
            # If switching to redaction mode, pending marks from *previous* pages should have already been cleared
            # by update_page_view. Marks on current page persist until applied or cleared by page/tool change.

        else: # Switching to pointer mode
            if self.current_tool_mode == "redaction": # If was in redaction, clear marks
                self._clear_pending_redactions()
            logging.debug("Mode Pointeur/Sélection activé."); self.current_tool_mode = "pointer" 
            self.statusBar().showMessage("Prêt."); self.pdf_view.setCursor(Qt.ArrowCursor)
            self._deselect_all_tool_actions_but_one(None)

    def _clear_pending_redactions(self):
        if hasattr(self, 'pending_redaction_items'): 
            for item in self.pending_redaction_items:
                if item.scene() == self.pdf_scene: 
                    self.pdf_scene.removeItem(item)
            self.pending_redaction_items = []
        if hasattr(self, 'pending_redactions'): 
            self.pending_redactions = []
        
        if hasattr(self, 'apply_redactions_action'):
            self.apply_redactions_action.setEnabled(False)


    def graphics_view_mouse_press(self, event: QMouseEvent): 
        scene_pos = self.pdf_view.mapToScene(event.pos())
        if self.current_tool_mode == "pointer": self._clear_selected_item_feedback() 

        if self.current_tool_mode == "pointer" and event.button() == Qt.LeftButton:
            pdf_point = fitz.Point(scene_pos.x() / self.current_zoom_factor, scene_pos.y() / self.current_zoom_factor)
            if self.current_pdf_document and self.current_page_number >= 0:
                page = self.current_pdf_document.load_page(self.current_page_number)
                self.selected_widget = None 
                for widget in page.widgets(): 
                    if widget.rect.contains(pdf_point): self.selected_widget = widget; break
                if self.selected_widget:
                    self.display_widget_properties(self.selected_widget)
                    bbox_scene = QRectF(self.selected_widget.rect.x0*self.current_zoom_factor, self.selected_widget.rect.y0*self.current_zoom_factor,
                                        self.selected_widget.rect.width*self.current_zoom_factor, self.selected_widget.rect.height*self.current_zoom_factor)
                    self.selected_annotation_bbox_item = QGraphicsRectItem(bbox_scene) 
                    pen = QPen(Qt.green, 2, Qt.DotLine); self.selected_annotation_bbox_item.setPen(pen)
                    self.pdf_scene.addItem(self.selected_annotation_bbox_item)
                    self.delete_selected_annot_action.setEnabled(False) 
                else: 
                    self.selected_annotation = None 
                    for annot in reversed(list(page.annots())): 
                        if not annot.is_widget and annot.rect.contains(pdf_point): self.selected_annotation = annot; break 
                    if self.selected_annotation:
                        self.delete_selected_annot_action.setEnabled(True)
                        self.display_annotation_properties(self.selected_annotation)
                        bbox_scene = QRectF(self.selected_annotation.rect.x0*self.current_zoom_factor, self.selected_annotation.rect.y0*self.current_zoom_factor,
                                            self.selected_annotation.rect.width*self.current_zoom_factor, self.selected_annotation.rect.height*self.current_zoom_factor)
                        self.selected_annotation_bbox_item = QGraphicsRectItem(bbox_scene)
                        pen = QPen(Qt.blue, 2, Qt.DotLine); self.selected_annotation_bbox_item.setPen(pen)
                        self.pdf_scene.addItem(self.selected_annotation_bbox_item)
        
        elif self.current_tool_mode in ["highlight", "rect_annot", "circle_annot", "freetext_annot", "insert_image", "redaction"] and event.button() == Qt.LeftButton: 
            self.selection_start_point = scene_pos
            if self.selection_rect_item: 
                if self.selection_rect_item.scene() == self.pdf_scene: self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            
            self.selection_rect_item = QGraphicsRectItem(QRectF(self.selection_start_point, self.selection_start_point))
            pen_color = Qt.black
            pen_style = Qt.DashLine
            if self.current_tool_mode in ["rect_annot", "circle_annot", "freetext_annot", "insert_image"]: 
                pen_color = QColor.fromRgbF(*(self.shape_border_color if self.shape_border_color else (0,0,0)))
            elif self.current_tool_mode == "redaction":
                pen_color = Qt.red
                # self.selection_rect_item.setBrush(QColor(0,0,0,30)) # Optional light fill for temp item

            pen = QPen(pen_color); pen.setStyle(pen_style)
            self.selection_rect_item.setPen(pen)
            self.pdf_scene.addItem(self.selection_rect_item)

        elif self.current_tool_mode == "line_annot" and event.button() == Qt.LeftButton:
            self.selection_start_point = scene_pos
            if self.selection_rect_item: 
                if self.selection_rect_item.scene() == self.pdf_scene: self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            self.selection_rect_item = QGraphicsLineItem(QLineF(self.selection_start_point, self.selection_start_point))
            pen = QPen(QColor.fromRgbF(*(self.shape_border_color if self.shape_border_color else (0,0,0))))
            pen.setWidthF(self.shape_border_width * self.current_zoom_factor); pen.setStyle(Qt.DashLine)
            self.selection_rect_item.setPen(pen); self.pdf_scene.addItem(self.selection_rect_item)
        
        elif self.current_tool_mode == "text_annot" and event.button() == Qt.LeftButton:
            self.selection_start_point = scene_pos
        
        elif self.current_tool_mode == "ink" and event.button() == Qt.LeftButton:
            self.current_ink_stroke = [scene_pos]
            if self.temp_ink_item: 
                if self.temp_ink_item.scene() == self.pdf_scene: self.pdf_scene.removeItem(self.temp_ink_item)
                self.temp_ink_item = None
            path = QPainterPath(self.current_ink_stroke[0])
            self.temp_ink_item = QGraphicsPathItem(path)
            pen = QPen(QColor.fromRgbF(*self.ink_color)); pen.setWidthF(self.ink_thickness * self.current_zoom_factor) 
            self.temp_ink_item.setPen(pen); self.pdf_scene.addItem(self.temp_ink_item)
        
        else: super(QGraphicsView, self.pdf_view).mousePressEvent(event)

    def graphics_view_mouse_move(self, event: QMouseEvent): 
        current_point = self.pdf_view.mapToScene(event.pos())
        if self.current_tool_mode in ["highlight", "rect_annot", "circle_annot", "freetext_annot", "insert_image", "redaction"] and self.selection_start_point:
            if self.selection_rect_item and isinstance(self.selection_rect_item, QGraphicsRectItem):
                self.selection_rect_item.setRect(QRectF(self.selection_start_point, current_point).normalized())
        elif self.current_tool_mode == "line_annot" and self.selection_start_point:
            if self.selection_rect_item and isinstance(self.selection_rect_item, QGraphicsLineItem):
                self.selection_rect_item.setLine(QLineF(self.selection_start_point, current_point))
        elif self.current_tool_mode == "ink" and self.current_ink_stroke:
            self.current_ink_stroke.append(current_point)
            if self.temp_ink_item:
                path = QPainterPath(self.current_ink_stroke[0])
                for p_stroke in self.current_ink_stroke[1:]: path.lineTo(p_stroke)
                self.temp_ink_item.setPath(path)
        else: super(QGraphicsView, self.pdf_view).mouseMoveEvent(event)

    def graphics_view_mouse_release(self, event: QMouseEvent): 
        end_point = self.pdf_view.mapToScene(event.pos())
        if self.selection_rect_item: # This is the temporary item for dragging
            if self.selection_rect_item.scene() == self.pdf_scene: self.pdf_scene.removeItem(self.selection_rect_item)
            self.selection_rect_item = None
        
        if event.button() == Qt.LeftButton and self.selection_start_point:
            final_rect_scene = QRectF(self.selection_start_point, end_point).normalized()
            
            if self.current_tool_mode == "redaction":
                if final_rect_scene.width() > 1 and final_rect_scene.height() > 1: # Avoid tiny accidental rects
                    persistent_redaction_mark = QGraphicsRectItem(final_rect_scene)
                    persistent_redaction_mark.setPen(QPen(Qt.red, 1, Qt.SolidLine))
                    persistent_redaction_mark.setBrush(QColor(0, 0, 0, 70)) # Semi-transparent black
                    self.pdf_scene.addItem(persistent_redaction_mark)
                    
                    self.pending_redaction_items.append(persistent_redaction_mark)
                    self.pending_redactions.append(final_rect_scene) 
                    self.apply_redactions_action.setEnabled(True)
                    logging.debug(f"Added pending redaction mark: {final_rect_scene}")
                else:
                    logging.debug("Redaction rectangle too small, not added.")

            elif self.current_tool_mode == "highlight": self.apply_highlight(final_rect_scene)
            elif self.current_tool_mode == "rect_annot": self.apply_rect_annot(final_rect_scene)
            elif self.current_tool_mode == "circle_annot": self.apply_circle_annot(final_rect_scene)
            elif self.current_tool_mode == "line_annot": self.apply_line_annot(self.selection_start_point, end_point) 
            elif self.current_tool_mode == "freetext_annot":
                if final_rect_scene.width() > 5 and final_rect_scene.height() > 5: self.apply_freetext_annot(final_rect_scene)
                else: self.freetext_annot_action.setChecked(False) 
            elif self.current_tool_mode == "insert_image":
                if final_rect_scene.width() > 5 and final_rect_scene.height() > 5: self.apply_insert_image(final_rect_scene)
                else: self.insert_image_action.setChecked(False)
            elif self.current_tool_mode == "text_annot":
                 if (self.selection_start_point - end_point).manhattanLength() < 5: self.apply_text_annot(self.selection_start_point) 
        
        if self.current_tool_mode == "ink" and self.current_ink_stroke and event.button() == Qt.LeftButton:
            if self.temp_ink_item: 
                if self.temp_ink_item.scene() == self.pdf_scene: self.pdf_scene.removeItem(self.temp_ink_item)
                self.temp_ink_item = None
            if len(self.current_ink_stroke) > 1: self.apply_ink(self.current_ink_stroke)
            self.current_ink_stroke = [] 
        
        if self.current_tool_mode != "pointer" : 
            self.selection_start_point = None 


    def apply_highlight(self, selection_rect_scene: QRectF): 
        if not self.current_pdf_document or self.current_page_number < 0: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_rect = fitz.Rect(selection_rect_scene.left() / self.current_zoom_factor, selection_rect_scene.top() / self.current_zoom_factor,
                             selection_rect_scene.right() / self.current_zoom_factor, selection_rect_scene.bottom() / self.current_zoom_factor)
        try: annot = page.add_highlight_annot(pdf_rect)
            if annot: annot.set_colors(stroke=self.highlight_color); annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Surlignage", f"Erreur: {e}")
    def apply_ink(self, list_of_points_scene): 
        if not self.current_pdf_document or self.current_page_number < 0 or not list_of_points_scene: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_points = [fitz.Point(p.x()/self.current_zoom_factor, p.y()/self.current_zoom_factor) for p in list_of_points_scene]
        if not pdf_points: return
        try: annot = page.add_ink_annot([pdf_points])
            if annot: annot.set_colors(stroke=self.ink_color); annot.set_line_width(self.ink_thickness); annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Dessin", f"Erreur: {e}")
    def apply_rect_annot(self, selection_rect_scene: QRectF): 
        if not self.current_pdf_document or self.current_page_number < 0: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_rect = fitz.Rect(selection_rect_scene.left()/self.current_zoom_factor, selection_rect_scene.top()/self.current_zoom_factor, selection_rect_scene.right()/self.current_zoom_factor, selection_rect_scene.bottom()/self.current_zoom_factor)
        try: annot = page.add_rect_annot(pdf_rect)
            if annot: annot.set_colors(stroke=self.shape_border_color, fill=self.shape_fill_color); annot.set_border(width=self.shape_border_width); annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Rectangle", f"Erreur: {e}")
    def apply_circle_annot(self, selection_rect_scene: QRectF): 
        if not self.current_pdf_document or self.current_page_number < 0: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_rect = fitz.Rect(selection_rect_scene.left()/self.current_zoom_factor, selection_rect_scene.top()/self.current_zoom_factor, selection_rect_scene.right()/self.current_zoom_factor, selection_rect_scene.bottom()/self.current_zoom_factor)
        try: annot = page.add_circle_annot(pdf_rect)
            if annot: annot.set_colors(stroke=self.shape_border_color, fill=self.shape_fill_color); annot.set_border(width=self.shape_border_width); annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Cercle", f"Erreur: {e}")
    def apply_line_annot(self, p1_scene: QPointF, p2_scene: QPointF): 
        if not self.current_pdf_document or self.current_page_number < 0: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        p1_pdf = fitz.Point(p1_scene.x()/self.current_zoom_factor, p1_scene.y()/self.current_zoom_factor); p2_pdf = fitz.Point(p2_scene.x()/self.current_zoom_factor, p2_scene.y()/self.current_zoom_factor)
        try: annot = page.add_line_annot(p1_pdf, p2_pdf)
            if annot: annot.set_colors(stroke=self.shape_border_color); annot.set_border(width=self.shape_border_width); annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Ligne", f"Erreur: {e}")
    def apply_text_annot(self, point_scene: QPointF): 
        if not self.current_pdf_document or self.current_page_number < 0: return
        text, ok = QInputDialog.getMultiLineText(self, "Ajouter Note", "Texte de la note :"); tool_active = self.text_annot_action.isChecked()
        if not (ok and text.strip()):
            if tool_active: self.text_annot_action.setChecked(False); return
        page = self.current_pdf_document.load_page(self.current_page_number); pdf_point = fitz.Point(point_scene.x()/self.current_zoom_factor, point_scene.y()/self.current_zoom_factor)
        try: annot = page.add_text_annot(pdf_point, text)
            if annot: annot.set_info(content=text); annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Note", f"Erreur: {e}")
        if tool_active: self.text_annot_action.setChecked(False)
    def apply_freetext_annot(self, selection_rect_scene: QRectF): 
        if not self.current_pdf_document or self.current_page_number < 0: return
        text, ok = QInputDialog.getMultiLineText(self, "Ajouter Zone Texte", "Texte :"); tool_active = self.freetext_annot_action.isChecked()
        if not (ok and text.strip()):
            if tool_active: self.freetext_annot_action.setChecked(False); return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_rect = fitz.Rect(selection_rect_scene.left()/self.current_zoom_factor, selection_rect_scene.top()/self.current_zoom_factor, selection_rect_scene.right()/self.current_zoom_factor, selection_rect_scene.bottom()/self.current_zoom_factor)
        try: annot = page.add_freetext_annot(pdf_rect, text, fontname=self.freetext_fontname, fontsize=self.freetext_fontsize, text_color=self.freetext_color)
            if annot: annot.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Zone Texte", f"Erreur: {e}")
        if tool_active: self.freetext_annot_action.setChecked(False)
    def apply_insert_image(self, selection_rect_scene: QRectF): 
        if not self.current_pdf_document or self.current_page_number < 0: if self.insert_image_action.isChecked(): self.insert_image_action.setChecked(False); return
        img_path, _ = QFileDialog.getOpenFileName(self, "Choisir Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)"); tool_active = self.insert_image_action.isChecked()
        if not img_path:
            if tool_active: self.insert_image_action.setChecked(False); return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_rect = fitz.Rect(selection_rect_scene.left()/self.current_zoom_factor, selection_rect_scene.top()/self.current_zoom_factor, selection_rect_scene.right()/self.current_zoom_factor, selection_rect_scene.bottom()/self.current_zoom_factor)
        try: page.insert_image(pdf_rect, filename=img_path); self.is_document_modified = True; self._refresh_page_and_thumbnail()
        except Exception as e: QMessageBox.critical(self, "Erreur Image", f"Erreur: {e}")
        if tool_active: self.insert_image_action.setChecked(False)

    def display_annotation_properties(self, annot: fitz.Annot): 
        self._clear_property_widgets() 
        if not annot: self.properties_label_info.setText("Aucune annotation sélectionnée."); return
        info_text = f"Type: {annot.type[1]}\nRect: {annot.rect}\nContenu: {annot.info.get('content', 'N/A')}"
        self.properties_label_info.setText(info_text)

    def display_widget_properties(self, widget: fitz.Widget):
        self._clear_property_widgets()
        if not widget: self.properties_label_info.setText("Aucun widget sélectionné."); return
        base_info = f"Nom: {widget.field_name}\nType: {widget.field_type_string}\n"
        self.properties_label_info.setText(base_info)
        self.update_field_action.setEnabled(False) 
        if widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
            line_edit = QLineEdit(str(widget.field_value if widget.field_value is not None else ""))
            line_edit.setObjectName("PropertyValueEdit"); line_edit.textChanged.connect(self.on_properties_text_changed) 
            self.property_widget_layout.addWidget(line_edit); self.current_prop_widgets.append(line_edit)
        elif widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
            checkbox = QCheckBox(f"Coché (Valeur: {widget.field_value})"); checkbox.setObjectName("PropertyValueEdit")
            checkbox.setChecked(bool(widget.field_value))
            checkbox.stateChanged.connect(lambda state, w=widget: self.apply_checkbox_or_radio_change(w, state == Qt.Checked))
            self.property_widget_layout.addWidget(checkbox); self.current_prop_widgets.append(checkbox)
        elif widget.field_type == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
            page = self.current_pdf_document.load_page(self.current_page_number); group_name = widget.field_name
            radio_group_box = QGroupBox(f"Groupe: {group_name}"); radio_layout = QVBoxLayout(); radio_button_group = QButtonGroup(self) 
            for i, w_in_group in enumerate(page.widgets()):
                if w_in_group.field_name == group_name and w_in_group.field_type == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
                    radio_text = f"Option: {w_in_group.field_value}"; radio_button = QRadioButton(radio_text)
                    radio_button.setObjectName(f"PropertyValueRadio_{i}"); radio_button.setChecked(w_in_group.value) 
                    radio_button.setProperty("pdf_widget", w_in_group); radio_button_group.addButton(radio_button)
                    radio_layout.addWidget(radio_button); self.current_prop_widgets.append(radio_button) 
                    radio_button.toggled.connect(lambda checked, rb_widget=w_in_group: self.apply_checkbox_or_radio_change(rb_widget, checked))
            radio_group_box.setLayout(radio_layout); self.property_widget_layout.addWidget(radio_group_box); self.current_prop_widgets.append(radio_group_box) 
        elif widget.field_type == fitz.PDF_WIDGET_TYPE_COMBOBOX or widget.field_type == fitz.PDF_WIDGET_TYPE_LISTBOX:
            is_cb = widget.field_type == fitz.PDF_WIDGET_TYPE_COMBOBOX; opts = widget.choice_values
            if not opts: self.property_widget_layout.addWidget(QLabel("Aucune option.")); return
            if is_cb:
                combo = QComboBox(); combo.setObjectName("PropertyValueEdit"); combo.addItems(opts if opts else [])
                try:
                    if widget.field_value in (opts or []): combo.setCurrentText(widget.field_value)
                    elif opts : combo.setCurrentIndex(0) 
                except Exception as e: logging.warning(f"Erreur ComboBox '{widget.field_name}': {e}")
                combo.currentIndexChanged.connect(self.apply_combobox_or_listbox_change)
                self.property_widget_layout.addWidget(combo); self.current_prop_widgets.append(combo)
            else: # ListBox
                lw = QListWidget(); lw.setObjectName("PropertyValueEdit"); lw.addItems(opts if opts else [])
                if widget.field_flags & fitz.PDF_FIELD_IS_MULTISELECT: lw.setSelectionMode(QAbstractItemView.ExtendedSelection)
                else: lw.setSelectionMode(QAbstractItemView.SingleSelection)
                if isinstance(widget.field_value, list): # Multi-select
                    for v_item in widget.field_value:
                        items = lw.findItems(v_item, Qt.MatchExactly)
                        if items: items[0].setSelected(True)
                elif isinstance(widget.field_value, str): # Single-select
                    items = lw.findItems(widget.field_value, Qt.MatchExactly)
                    if items: items[0].setSelected(True)
                lw.itemSelectionChanged.connect(self.apply_combobox_or_listbox_change)
                self.property_widget_layout.addWidget(lw); self.current_prop_widgets.append(lw)
        else:
            val_label = QLabel(f"Valeur: {widget.field_value if widget.field_value is not None else 'N/A'}\n(Édition non supportée)")
            self.property_widget_layout.addWidget(val_label); self.current_prop_widgets.append(val_label)

    def on_properties_text_changed(self): 
        if self.selected_widget and self.current_prop_widgets and isinstance(self.current_prop_widgets[0], QLineEdit):
            self.update_field_action.setEnabled(True) 

    def apply_widget_value_change(self): 
        if not self.selected_widget: return
        new_value = None; prop_widget = self.current_prop_widgets[0] if self.current_prop_widgets else None
        if isinstance(prop_widget, QLineEdit): new_value = prop_widget.text()
        if new_value is not None and self.selected_widget.field_value != new_value and self.selected_widget.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
            try: self.selected_widget.field_value = new_value; self.selected_widget.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail(); self.statusBar().showMessage(f"Champ '{self.selected_widget.field_name}' MàJ.")
            except Exception as e: QMessageBox.critical(self, "Erreur MàJ Champ", f"Erreur: {e}")

    def apply_checkbox_or_radio_change(self, pdf_widget_target: fitz.Widget, is_checked: bool):
        if not pdf_widget_target: return
        new_value = is_checked 
        if pdf_widget_target.value != new_value: 
            try:
                pdf_widget_target.value = new_value 
                pdf_widget_target.update()
                self.is_document_modified = True; self._refresh_page_and_thumbnail()
                self.statusBar().showMessage(f"Champ '{pdf_widget_target.field_name}' MàJ.")
            except Exception as e: QMessageBox.critical(self, "Erreur MàJ Champ", f"Erreur: {e}")

    def apply_combobox_or_listbox_change(self):
        if not self.selected_widget or not self.current_prop_widgets: return
        prop_widget = self.current_prop_widgets[0]; new_value = None
        if isinstance(prop_widget, QComboBox): new_value = prop_widget.currentText()
        elif isinstance(prop_widget, QListWidget):
            sel_items = prop_widget.selectedItems()
            if self.selected_widget.field_flags & fitz.PDF_FIELD_IS_MULTISELECT: new_value = [item.text() for item in sel_items]
            elif sel_items: new_value = sel_items[0].text()
            else: new_value = "" 
        if new_value is not None and self.selected_widget.field_value != new_value:
            try: self.selected_widget.field_value = new_value; self.selected_widget.update(); self.is_document_modified = True; self._refresh_page_and_thumbnail(); self.statusBar().showMessage(f"Champ '{self.selected_widget.field_name}' MàJ.")
            except Exception as e: QMessageBox.critical(self, "Erreur MàJ Champ", f"Erreur: {e}")

    def _refresh_page_and_thumbnail(self): 
        self.update_page_view() # This will also clear pending redactions for the current page
        if self.current_pdf_document and 0 <= self.current_page_number < self.page_thumbnails_list.count():
            list_item = self.page_thumbnails_list.item(self.current_page_number)
            if list_item:
                page_for_thumb = self.current_pdf_document.load_page(self.current_page_number)
                thumb_matrix = fitz.Matrix(0.2, 0.2); pix = page_for_thumb.get_pixmap(matrix=thumb_matrix)
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888)
                list_item.setIcon(QIcon(QPixmap.fromImage(qimage)))
        self.save_action.setEnabled(True)

    # --- Nouvelles méthodes pour l'extraction de texte ---
    def extract_text_current_page(self):
        if not self.current_pdf_document or self.current_page_number < 0:
            QMessageBox.warning(self, "Aucune page", "Aucune page n'est actuellement affichée.")
            return
        try:
            page = self.current_pdf_document.load_page(self.current_page_number)
            text = page.get_text("text")
            self._show_extracted_text_dialog(text, f"Texte de la Page {self.current_page_number + 1}")
        except Exception as e:
            logging.error(f"Erreur extraction texte page {self.current_page_number}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'Extraction", f"Impossible d'extraire le texte: {e}")

    def extract_text_entire_document(self):
        if not self.current_pdf_document:
            QMessageBox.warning(self, "Aucun document", "Aucun document n'est ouvert.")
            return
        try:
            full_text = ""
            for i in range(self.current_pdf_document.page_count):
                page = self.current_pdf_document.load_page(i)
                full_text += f"--- Page {i+1} ---\n"
                full_text += page.get_text("text")
                full_text += "\n\n"
            self._show_extracted_text_dialog(full_text, "Texte du Document Entier")
        except Exception as e:
            logging.error(f"Erreur extraction texte document: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'Extraction", f"Impossible d'extraire le texte du document: {e}")

    def _show_extracted_text_dialog(self, text_content, title):
        dialog = TextDisplayDialog(text_content, title, self)
        dialog.exec_()

    # --- Nouvelle méthode pour l'extraction d'images ---
    def extract_images_from_document(self):
        if not self.current_pdf_document:
            QMessageBox.warning(self, "Aucun Document", "Veuillez ouvrir un document PDF d'abord.")
            return

        folder_path = QFileDialog.getExistingDirectory(self, "Choisir le dossier de destination pour les images")
        if not folder_path:
            return

        extracted_count = 0
        try:
            for page_num in range(self.current_pdf_document.page_count):
                page = self.current_pdf_document.load_page(page_num)
                image_list = page.get_images(full=True)
                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = self.current_pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    image_filename = os.path.join(folder_path, f"page{page_num + 1}_img{img_index + 1}_{xref}.{image_ext}")
                    with open(image_filename, "wb") as img_file:
                        img_file.write(image_bytes)
                    extracted_count += 1
            
            if extracted_count > 0:
                QMessageBox.information(self, "Extraction Réussie", f"{extracted_count} image(s) extraite(s) avec succès dans {folder_path}.")
            else:
                QMessageBox.information(self, "Aucune Image", "Aucune image trouvée dans le document.")
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction des images: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'Extraction d'Images", f"Une erreur est survenue: {e}")

    # --- Fusion et Division ---
    def merge_pdfs(self):
        if not self._ask_save_before_action(): return # Demander si le doc courant doit être sauvé

        source_files, _ = QFileDialog.getOpenFileNames(self, "Sélectionner les PDF à fusionner", "", "Fichiers PDF (*.pdf)")
        if not source_files or len(source_files) < 1: # On peut fusionner un seul fichier pour le "nettoyer" ou le restructurer
            return

        dest_file, _ = QFileDialog.getSaveFileName(self, "Enregistrer le PDF fusionné sous...", "", "Fichiers PDF (*.pdf)")
        if not dest_file:
            return

        result_pdf = fitz.open() # Document vide
        try:
            for pdf_path in source_files:
                source_doc = fitz.open(pdf_path)
                result_pdf.insert_pdf(source_doc)
                source_doc.close()
            
            result_pdf.save(dest_file, garbage=3, deflate=True)
            result_pdf.close()
            QMessageBox.information(self, "Fusion Réussie", f"Les PDF ont été fusionnés avec succès en :\n{dest_file}")
        except Exception as e:
            if 'result_pdf' in locals() and result_pdf.is_open: result_pdf.close()
            logging.error(f"Erreur lors de la fusion des PDF: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de Fusion", f"Une erreur est survenue lors de la fusion: {e}")
    
    def split_pdf_each_page(self):
        if not self.current_pdf_document:
            QMessageBox.warning(self, "Aucun Document", "Veuillez ouvrir un document PDF à diviser.")
            return

        output_folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier de destination pour les pages divisées")
        if not output_folder:
            return

        base_filename = "page"
        if self.current_pdf_document.name and self.current_pdf_document.name != "stdin":
             base_filename = os.path.splitext(os.path.basename(self.current_pdf_document.name))[0]
        
        num_pages = self.current_pdf_document.page_count
        split_count = 0
        errors = []

        try:
            for i in range(num_pages):
                new_doc = fitz.open() # Nouveau PDF vide
                new_doc.insert_pdf(self.current_pdf_document, from_page=i, to_page=i) # Insérer la page i
                
                output_filename = os.path.join(output_folder, f"{base_filename}_page_{i + 1}.pdf")
                new_doc.save(output_filename, garbage=3, deflate=True)
                new_doc.close()
                split_count += 1
            
            if not errors:
                QMessageBox.information(self, "Division Réussie", 
                                        f"{split_count} page(s) divisée(s) avec succès dans {output_folder}.")
            else:
                QMessageBox.warning(self, "Division Partielle", 
                                    f"{split_count} page(s) divisée(s).\nErreurs survenues pour : {', '.join(errors)}.")
        except Exception as e:
            logging.error(f"Erreur lors de la division du PDF: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de Division", f"Une erreur majeure est survenue: {e}")
            if 'new_doc' in locals() and new_doc.is_open: new_doc.close()

    def _parse_page_ranges(self, range_string: str, doc_total_pages: int) -> list | str:
        output_file_page_lists = []
        if not range_string.strip():
            return "Erreur: La chaîne de plages est vide."

        parts = range_string.split(',')

        for part_string in parts:
            part_string = part_string.strip()
            if not part_string:
                continue  # Skip empty parts that might result from "1,,2" or trailing commas

            current_part_pages_set = set()
            
            if '-' in part_string:
                if part_string.count('-') > 1:
                    return f"Erreur: Format de plage invalide dans '{part_string}'. Trop de tirets."
                
                start_str, end_str = part_string.split('-', 1)
                start_str = start_str.strip()
                end_str = end_str.strip()

                if not start_str or not end_str:
                     return f"Erreur: Numéro de début ou de fin manquant dans la plage '{part_string}'."

                try:
                    start_num = int(start_str)
                except ValueError:
                    return f"Erreur: Numéro de début non valide dans la plage '{part_string}'."

                try:
                    if end_str.lower() == 'fin': # French 'end'
                        end_num = doc_total_pages
                    elif end_str.lower() == 'end': # English 'end'
                        end_num = doc_total_pages
                    else:
                        end_num = int(end_str)
                except ValueError:
                    return f"Erreur: Numéro de fin non valide dans la plage '{part_string}'."

                if not (1 <= start_num <= doc_total_pages):
                    return f"Erreur: Numéro de page de début {start_num} hors limites (1-{doc_total_pages}) dans '{part_string}'."
                if not (1 <= end_num <= doc_total_pages):
                    return f"Erreur: Numéro de page de fin {end_num} hors limites (1-{doc_total_pages}) dans '{part_string}'."
                if start_num > end_num:
                    return f"Erreur: Le numéro de page de début {start_num} est supérieur au numéro de fin {end_num} dans '{part_string}'."

                for p in range(start_num, end_num + 1):
                    current_part_pages_set.add(p - 1)
            else: # Single page number
                try:
                    pageNum = int(part_string)
                except ValueError:
                    return f"Erreur: Numéro de page non valide '{part_string}'."
                
                if not (1 <= pageNum <= doc_total_pages):
                    return f"Erreur: Numéro de page {pageNum} hors limites (1-{doc_total_pages}) dans '{part_string}'."
                current_part_pages_set.add(pageNum - 1)
            
            if current_part_pages_set:
                output_file_page_lists.append(sorted(list(current_part_pages_set)))
        
        if not output_file_page_lists:
            return "Erreur: Aucune page ou plage valide n'a été spécifiée pour créer des fichiers de sortie."
            
        return output_file_page_lists

    def split_pdf_by_range(self):
        if not self.current_pdf_document:
            QMessageBox.warning(self, "Aucun Document", "Veuillez ouvrir un document PDF d'abord.")
            return

        dialog = PageRangeDialog(self.current_pdf_document.page_count, self)
        dialog_result = dialog.exec_()

        if dialog_result == QDialog.Accepted:
            range_str = dialog.get_range_string().strip()
            if not range_str:
                QMessageBox.warning(self, "Entrée Requise", "Veuillez entrer les plages de pages.")
                return

            page_lists_for_files = self._parse_page_ranges(range_str, self.current_pdf_document.page_count)

            if isinstance(page_lists_for_files, str): # Error message returned
                QMessageBox.critical(self, "Erreur de Plage", page_lists_for_files)
                return
            
            if not page_lists_for_files: # Should be caught by parser, but as a safeguard
                QMessageBox.information(self, "Aucune Page Sélectionnée", "Aucune page valide n'a été sélectionnée avec les plages fournies.")
                return

            output_dir = QFileDialog.getExistingDirectory(self, "Sélectionner le Dossier de Sortie")
            if not output_dir:
                return # User cancelled directory selection

            base_name = os.path.splitext(os.path.basename(self.current_pdf_document.name or "document"))[0]
            files_created_count = 0
            
            try:
                for i, pages_for_one_file in enumerate(page_lists_for_files):
                    if not pages_for_one_file: # Should not happen if parser is correct
                        logging.warning(f"Bloc de pages vide rencontré pour la partie {i+1}, ignoré.")
                        continue

                    new_pdf = fitz.open()
                    for page_index in pages_for_one_file: # pages are 0-indexed
                        new_pdf.insert_pdf(self.current_pdf_document, from_page=page_index, to_page=page_index)
                    
                    output_path = os.path.join(output_dir, f"{base_name}_partie_{i+1}.pdf")
                    new_pdf.save(output_path, garbage=3, deflate=True)
                    new_pdf.close()
                    files_created_count += 1
                
                if files_created_count > 0:
                    QMessageBox.information(self, "Division Réussie", 
                                            f"{files_created_count} fichier(s) créé(s) avec succès dans {output_dir}.")
                else:
                    # This case should ideally be caught by parser returning an error for "No valid pages..."
                    QMessageBox.information(self, "Division Terminée", 
                                            "Aucun fichier n'a été créé. Veuillez vérifier vos plages de pages.")
            except Exception as e:
                logging.error(f"Erreur lors de la division par plage: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur de Division", f"Une erreur est survenue: {e}")
                if 'new_pdf' in locals() and new_pdf.is_open: new_pdf.close()

    def _set_redaction_fill_color(self):
        current_color_qt = QColor(
            int(self.redaction_fill_color[0] * 255),
            int(self.redaction_fill_color[1] * 255),
            int(self.redaction_fill_color[2] * 255)
        )
        color = QColorDialog.getColor(current_color_qt, self, "Choisir la couleur de remplissage pour la rédaction")
        if color.isValid():
            self.redaction_fill_color = (color.redF(), color.greenF(), color.blueF())
            logging.info(f"Couleur de remplissage de rédaction définie sur : {self.redaction_fill_color}")

    def _set_redaction_overlay_text(self):
        text, ok = QInputDialog.getText(self, "Texte Superposé pour Rédaction", 
                                        "Entrez le texte à superposer (laissez vide pour aucun texte):", 
                                        QLineEdit.Normal, self.redaction_overlay_text)
        if ok:
            self.redaction_overlay_text = text
            logging.info(f"Texte superposé de rédaction défini sur : '{self.redaction_overlay_text}'")


    def apply_redactions_on_current_page(self):
        if not self.current_pdf_document or self.current_page_number < 0:
            QMessageBox.warning(self, "Aucun Document/Page", "Aucun document ou page valide n'est sélectionné.")
            return

        if not self.pending_redactions:
            QMessageBox.information(self, "Aucune Marque", "Aucune marque de rédaction à appliquer.")
            return

        reply = QMessageBox.question(self, "Appliquer les Rédactions", 
                                     "Ceci va supprimer définitivement le contenu sous les marques de rédaction sur la page actuelle. Continuer?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                page = self.current_pdf_document.load_page(self.current_page_number)
                
                for q_rect_scene in self.pending_redactions:
                    pdf_x0 = q_rect_scene.left() / self.current_zoom_factor
                    pdf_y0 = q_rect_scene.top() / self.current_zoom_factor
                    pdf_x1 = q_rect_scene.right() / self.current_zoom_factor
                    pdf_y1 = q_rect_scene.bottom() / self.current_zoom_factor
                    pdf_rect = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1).normalize()
                    
                    annot_params = {
                        "fill": self.redaction_fill_color
                    }
                    if self.redaction_overlay_text:
                        annot_params["text"] = self.redaction_overlay_text
                        annot_params["fontname"] = self.redaction_fontname
                        annot_params["fontsize"] = self.redaction_fontsize
                        annot_params["text_color"] = self.redaction_text_color
                        annot_params["align"] = fitz.TEXT_ALIGN_CENTER 
                        # Note: PyMuPDF might auto-adjust fontsize if it's 0 to fit the text.
                        # If specific size is desired and text is too long, it might get clipped or look bad.
                        # More advanced text fitting might be needed for complex cases.

                    page.add_redact_annot(pdf_rect, **annot_params)
                                
                page.apply_redactions() # Actually remove content
                self.is_document_modified = True
                
                self._clear_pending_redactions() # Clears lists and visual items, disables apply action
                
                self._refresh_page_and_thumbnail() # Update view to show redacted content
                self.statusBar().showMessage("Rédactions appliquées à la page actuelle.")
                logging.info(f"Redactions applied to page {self.current_page_number + 1}")

            except Exception as e:
                logging.error(f"Erreur lors de l'application des rédactions: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur de Rédaction", f"Une erreur est survenue: {e}")
                # Optionally, try to restore visual marks if apply failed mid-way, though complex.
                # For now, just clear them as something went wrong.
                self._clear_pending_redactions()
                self._refresh_page_and_thumbnail() # Refresh to show current state after error


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
