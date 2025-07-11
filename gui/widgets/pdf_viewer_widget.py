# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import logging
import os
from PyQt5.QtGui import QMouseEvent


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QSizePolicy, QSpinBox, QWidget,
    QScrollArea, QApplication, QMessageBox, QCheckBox, QLineEdit,
    QSplitter, QTabWidget, QListWidget, QTreeWidget, QTreeWidgetItem, QListWidgetItem,
    QToolButton, QFileDialog, QGraphicsEllipseItem, QColorDialog, QInputDialog
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QPen, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QCoreApplication, QSize, QThread, pyqtSignal, QObject, QPointF


class PdfViewerWidget(QDialog):
    documentSavedAsNewVersion = pyqtSignal(str, str)


    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.current_pdf_document = None
        self.current_page_number = 0
        self.current_zoom_factor = 1.0
        self.current_view_rotation_angle = 0

        self.search_term = ""
        self.all_search_results_map = {}
        self.current_flat_results_list = []
        self.current_search_highlight_idx = -1
        self.search_highlight_item = None

        self.left_panel_tab_widget = None
        self.thumbnail_list_widget = None
        self.bookmark_tree_widget = None
        self.thumbnail_loader_thread = None

        self.annotation_mode_active = False
        self.document_modified_by_annotation = False
        self.current_annotation_tool = None
        self.annotation_toolbar = None
        self.highlight_tool_button = None
        self.ink_tool_button = None
        self.rect_tool_button = None
        self.circle_tool_button = None
        self.delete_annotation_button = None # Pour la suppression

        self.current_stroke_color = QColor("red")
        self.current_highlight_color = QColor(255, 255, 0, 180)
        self.current_stroke_width = 1.5

        self.mouse_press_pos_scene = None
        self.current_selection_rect_item = None
        self.current_selection_ellipse_item = None
        self.current_ink_stroke_points_scene = []
        self.current_ink_preview_item = None

        self.selected_annotation_object = None # Pour stocker l'objet annot PyMuPDF sélectionné
        self.selected_annotation_bbox_item = None # Pour visualiser la sélection

        self.setWindowTitle(self.tr("Visionneuse PDF - {0}").format(pdf_path))
        self.setMinimumSize(1000, 700)
        self.setModal(True)
        self._setup_ui()
        self._load_pdf()

    def tr(self, text, disambiguation=None, n=-1):
        return QCoreApplication.translate("PdfViewerWidget", text, disambiguation, n)

    def _setup_ui(self):
        overall_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        overall_layout.addWidget(splitter)

        self.left_panel_tab_widget = QTabWidget()
        self.left_panel_tab_widget.setMinimumWidth(200); self.left_panel_tab_widget.setMaximumWidth(400)
        self.thumbnail_list_widget = QListWidget()
        self.thumbnail_list_widget.setIconSize(QSize(100, 140)); self.thumbnail_list_widget.setViewMode(QListWidget.IconMode)
        self.thumbnail_list_widget.setResizeMode(QListWidget.Adjust); self.thumbnail_list_widget.setMovement(QListWidget.Static)
        self.thumbnail_list_widget.itemClicked.connect(self._on_thumbnail_clicked)
        self.left_panel_tab_widget.addTab(self.thumbnail_list_widget, self.tr("Miniatures"))
        self.bookmark_tree_widget = QTreeWidget(); self.bookmark_tree_widget.setHeaderLabel(self.tr("Signets"))
        self.bookmark_tree_widget.itemClicked.connect(self._on_bookmark_clicked)
        self.left_panel_tab_widget.addTab(self.bookmark_tree_widget, self.tr("Signets"))
        splitter.addWidget(self.left_panel_tab_widget)

        right_panel_widget = QWidget(); main_layout = QVBoxLayout(right_panel_widget)
        controls_widget = QWidget(); controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        self.toggle_annotation_mode_button = QToolButton(); self.toggle_annotation_mode_button.setText(self.tr("Annoter"))
        self.toggle_annotation_mode_button.setToolTip(self.tr("Activer/Désactiver le mode annotation")); self.toggle_annotation_mode_button.setCheckable(True)
        self.toggle_annotation_mode_button.setChecked(self.annotation_mode_active); self.toggle_annotation_mode_button.toggled.connect(self._on_toggle_annotation_mode)
        self.toggle_annotation_mode_button.setEnabled(False); controls_layout.addWidget(self.toggle_annotation_mode_button)

        self.save_annotations_button = QPushButton(QIcon.fromTheme("document-save", QIcon(":/icons/save.svg")), self.tr("Enregistrer"))
        self.save_annotations_button.setToolTip(self.tr("Enregistrer les modifications (nouvelle version)")); self.save_annotations_button.clicked.connect(self._save_annotated_document)
        self.save_annotations_button.setEnabled(False); controls_layout.addWidget(self.save_annotations_button); controls_layout.addSpacing(15)

        self.prev_page_button = QPushButton(QIcon.fromTheme("go-previous", QIcon(":/icons/arrow-left-circle.svg")), self.tr("< Préc."))
        self.prev_page_button.setToolTip(self.tr("Page précédente")); self.prev_page_button.clicked.connect(self.go_to_previous_page)
        self.prev_page_button.setEnabled(False); controls_layout.addWidget(self.prev_page_button)
        self.page_spinbox = QSpinBox(); self.page_spinbox.setMinimum(1); self.page_spinbox.setToolTip(self.tr("Aller à la page"))
        self.page_spinbox.setEnabled(False); self.page_spinbox.valueChanged.connect(self.go_to_page_from_spinbox); controls_layout.addWidget(self.page_spinbox)
        self.total_pages_label = QLabel(self.tr("/ N/A")); controls_layout.addWidget(self.total_pages_label)
        self.next_page_button = QPushButton(QIcon.fromTheme("go-next", QIcon(":/icons/arrow-right-circle.svg")), self.tr("Suiv. >"))
        self.next_page_button.setToolTip(self.tr("Page suivante")); self.next_page_button.clicked.connect(self.go_to_next_page)
        self.next_page_button.setEnabled(False); controls_layout.addWidget(self.next_page_button); controls_layout.addStretch()
        self.zoom_out_button = QPushButton(QIcon.fromTheme("zoom-out", QIcon(":/icons/zoom-out.svg")), self.tr("Zoom -"))
        self.zoom_out_button.setToolTip(self.tr("Zoom arrière")); self.zoom_out_button.clicked.connect(lambda: self.zoom(0.9))
        self.zoom_out_button.setEnabled(False); controls_layout.addWidget(self.zoom_out_button)
        self.zoom_in_button = QPushButton(QIcon.fromTheme("zoom-in", QIcon(":/icons/zoom-in.svg")), self.tr("Zoom +"))
        self.zoom_in_button.setToolTip(self.tr("Zoom avant")); self.zoom_in_button.clicked.connect(lambda: self.zoom(1.1))
        self.zoom_in_button.setEnabled(False); controls_layout.addWidget(self.zoom_in_button)
        self.zoom_original_button = QPushButton(QIcon.fromTheme("zoom-original", QIcon(":/icons/zoom-original.svg")), self.tr("Zoom 100%"))
        self.zoom_original_button.setToolTip(self.tr("Zoom original (100%)")); self.zoom_original_button.clicked.connect(lambda: self.set_zoom_factor(1.0))
        self.zoom_original_button.setEnabled(False); controls_layout.addWidget(self.zoom_original_button)
        self.zoom_fit_page_button = QPushButton(QIcon.fromTheme("zoom-fit-best", QIcon(":/icons/zoom-fit-page.svg")), self.tr("Ajuster Page"))
        self.zoom_fit_page_button.setToolTip(self.tr("Ajuster à la page entière")); self.zoom_fit_page_button.clicked.connect(self.zoom_to_fit_page)
        self.zoom_fit_page_button.setEnabled(False); controls_layout.addWidget(self.zoom_fit_page_button)
        self.zoom_fit_width_button = QPushButton(QIcon.fromTheme("zoom-fit-width", QIcon(":/icons/zoom-fit-width.svg")), self.tr("Ajuster Largeur"))
        self.zoom_fit_width_button.setToolTip(self.tr("Ajuster à la largeur de la page")); self.zoom_fit_width_button.clicked.connect(self.zoom_to_fit_width)
        self.zoom_fit_width_button.setEnabled(False); controls_layout.addWidget(self.zoom_fit_width_button); controls_layout.addSpacing(20)
        self.rotate_ccw_button = QPushButton(QIcon.fromTheme("object-rotate-left", QIcon(":/icons/rotate-ccw.svg")), self.tr("Rot. Gauche"))
        self.rotate_ccw_button.setToolTip(self.tr("Rotation anti-horaire")); self.rotate_ccw_button.clicked.connect(lambda: self.rotate_view(-90))
        self.rotate_ccw_button.setEnabled(False); controls_layout.addWidget(self.rotate_ccw_button)
        self.rotate_cw_button = QPushButton(QIcon.fromTheme("object-rotate-right", QIcon(":/icons/rotate-cw.svg")), self.tr("Rot. Droite"))
        self.rotate_cw_button.setToolTip(self.tr("Rotation horaire")); self.rotate_cw_button.clicked.connect(lambda: self.rotate_view(90))
        self.rotate_cw_button.setEnabled(False); controls_layout.addWidget(self.rotate_cw_button)
        main_layout.addWidget(controls_widget)

        self.annotation_toolbar = QWidget(); annotation_toolbar_layout = QHBoxLayout(self.annotation_toolbar)
        annotation_toolbar_layout.setContentsMargins(5,0,5,5)
        self.highlight_tool_button = QToolButton(); self.highlight_tool_button.setText(self.tr("Surligner")); self.highlight_tool_button.setToolTip(self.tr("Outil de surlignage"))
        self.highlight_tool_button.setCheckable(True); self.highlight_tool_button.setIcon(QIcon.fromTheme("format-text-highlight", QIcon(":/icons/highlight.svg")))
        self.highlight_tool_button.clicked.connect(lambda: self._set_annotation_tool("highlighter")); annotation_toolbar_layout.addWidget(self.highlight_tool_button)
        self.ink_tool_button = QToolButton(); self.ink_tool_button.setText(self.tr("Stylo")); self.ink_tool_button.setToolTip(self.tr("Outil de dessin libre (stylo)"))
        self.ink_tool_button.setCheckable(True); self.ink_tool_button.setIcon(QIcon.fromTheme("accessories-pencil", QIcon(":/icons/ink.svg")))
        self.ink_tool_button.clicked.connect(lambda: self._set_annotation_tool("ink")); annotation_toolbar_layout.addWidget(self.ink_tool_button)
        self.rect_tool_button = QToolButton(); self.rect_tool_button.setText(self.tr("Rectangle")); self.rect_tool_button.setToolTip(self.tr("Outil Rectangle"))
        self.rect_tool_button.setCheckable(True); self.rect_tool_button.setIcon(QIcon.fromTheme("draw-rectangle", QIcon(":/icons/rectangle.svg")))
        self.rect_tool_button.clicked.connect(lambda: self._set_annotation_tool("rectangle")); annotation_toolbar_layout.addWidget(self.rect_tool_button)
        self.circle_tool_button = QToolButton(); self.circle_tool_button.setText(self.tr("Cercle")); self.circle_tool_button.setToolTip(self.tr("Outil Cercle/Ellipse"))
        self.circle_tool_button.setCheckable(True); self.circle_tool_button.setIcon(QIcon.fromTheme("draw-ellipse", QIcon(":/icons/circle.svg")))
        self.circle_tool_button.clicked.connect(lambda: self._set_annotation_tool("circle")); annotation_toolbar_layout.addWidget(self.circle_tool_button)

        self.delete_annotation_button = QPushButton(QIcon.fromTheme("edit-delete", QIcon(":/icons/trash-2.svg")), self.tr("Supprimer Annot."))
        self.delete_annotation_button.setToolTip(self.tr("Supprimer l'annotation sélectionnée"))
        self.delete_annotation_button.clicked.connect(self._delete_selected_annotation)
        self.delete_annotation_button.setEnabled(False)
        annotation_toolbar_layout.addWidget(self.delete_annotation_button)

        annotation_toolbar_layout.addSpacing(10)
        self.stroke_color_button = QPushButton(self.tr("Couleur Trait")); self.stroke_color_button.setToolTip(self.tr("Choisir la couleur pour le stylo et les contours"))
        self.stroke_color_button.clicked.connect(self._choose_stroke_color); annotation_toolbar_layout.addWidget(self.stroke_color_button)
        self.stroke_width_button = QPushButton(self.tr("Épaisseur Trait")); self.stroke_width_button.setToolTip(self.tr("Choisir l'épaisseur pour le stylo et les contours"))
        self.stroke_width_button.clicked.connect(self._choose_stroke_width); annotation_toolbar_layout.addWidget(self.stroke_width_button)
        self.highlight_color_button = QPushButton(self.tr("Couleur Surlignage")); self.highlight_color_button.setToolTip(self.tr("Choisir la couleur du surlignage"))
        self.highlight_color_button.clicked.connect(self._choose_highlight_color); annotation_toolbar_layout.addWidget(self.highlight_color_button)
        annotation_toolbar_layout.addStretch(); self.annotation_toolbar.setVisible(False); main_layout.addWidget(self.annotation_toolbar)

        search_widget = QWidget(); search_layout = QHBoxLayout(search_widget); search_layout.setContentsMargins(5,0,5,5)
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText(self.tr("Rechercher dans le PDF...")); self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._on_search_triggered); search_layout.addWidget(self.search_input)
        self.search_case_sensitive_checkbox = QCheckBox(self.tr("Sensible à la casse")); search_layout.addWidget(self.search_case_sensitive_checkbox)
        self.search_button = QPushButton(QIcon.fromTheme("edit-find", QIcon(":/icons/search.svg")), self.tr("Chercher")); self.search_button.clicked.connect(self._on_search_triggered); search_layout.addWidget(self.search_button)
        self.search_prev_button = QPushButton(QIcon.fromTheme("go-up", QIcon(":/icons/chevron-up.svg")), self.tr("Précédent")); self.search_prev_button.clicked.connect(lambda: self._navigate_search_results(direction=-1))
        self.search_prev_button.setEnabled(False); search_layout.addWidget(self.search_prev_button)
        self.search_next_button = QPushButton(QIcon.fromTheme("go-down", QIcon(":/icons/chevron-down.svg")), self.tr("Suivant")); self.search_next_button.clicked.connect(lambda: self._navigate_search_results(direction=1))
        self.search_next_button.setEnabled(False); search_layout.addWidget(self.search_next_button)
        self.search_results_label = QLabel(""); search_layout.addWidget(self.search_results_label); search_layout.addStretch(); main_layout.addWidget(search_widget)

        self.pdf_view = QGraphicsView(); self.pdf_view.mousePressEvent = self.graphics_view_mouse_press; self.pdf_view.mouseMoveEvent = self.graphics_view_mouse_move
        self.pdf_view.mouseReleaseEvent = self.graphics_view_mouse_release; self.pdf_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate); self.pdf_view.setInteractive(True)
        self.pdf_scene = QGraphicsScene(self); self.pdf_view.setScene(self.pdf_scene); self.pdf_view_item = QGraphicsPixmapItem(); self.pdf_scene.addItem(self.pdf_view_item)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setWidget(self.pdf_view); main_layout.addWidget(scroll_area)
        close_button = QPushButton(QIcon.fromTheme("window-close", QIcon(":/icons/x-circle.svg")), self.tr("Fermer"))
        close_button.setToolTip(self.tr("Fermer la visionneuse")); close_button.clicked.connect(self.accept)
        button_bar_layout = QHBoxLayout(); button_bar_layout.addStretch(); button_bar_layout.addWidget(close_button); main_layout.addLayout(button_bar_layout)
        splitter.addWidget(right_panel_widget); splitter.setSizes([self.width() // 4, 3 * self.width() // 4])

    def _clear_selection_feedback(self):
        if self.selected_annotation_bbox_item and self.selected_annotation_bbox_item.scene():
            self.pdf_scene.removeItem(self.selected_annotation_bbox_item)
        self.selected_annotation_bbox_item = None
        self.selected_annotation_object = None
        if hasattr(self, 'delete_annotation_button'): # S'assurer que le bouton existe
            self.delete_annotation_button.setEnabled(False)

    def _load_pdf(self):
        self._clear_selection_feedback()
        # ... (reste de la méthode _load_pdf)
        try:
            self.current_pdf_document = fitz.open(self.pdf_path)
            if self.current_pdf_document.page_count > 0:
                self.current_page_number = 0; self.document_modified_by_annotation = False
                self.annotation_mode_active = False; self.toggle_annotation_mode_button.setChecked(False)
                self.save_annotations_button.setEnabled(False); self._set_annotation_tool(None)
                self.update_page_view(); self.update_navigation_controls()
                self.toggle_annotation_mode_button.setEnabled(True)
                self._load_thumbnails(); self._load_bookmarks()
            else:
                self.total_pages_label.setText(self.tr("Document vide")); self._disable_all_controls()
                self.thumbnail_list_widget.clear(); self.bookmark_tree_widget.clear()
        except Exception as e:
            logging.error(f"Erreur PDF '{self.pdf_path}': {e}", exc_info=True); self.total_pages_label.setText(self.tr("Erreur: {0}").format(str(e)))
            self._disable_all_controls(); self.thumbnail_list_widget.clear(); self.bookmark_tree_widget.clear()
            QMessageBox.critical(self, self.tr("Erreur PDF"), self.tr("Impossible d'ouvrir PDF '{0}'.\nErreur: {1}").format(self.pdf_path, str(e)))

    def update_page_view(self):
        self._clear_selection_feedback() # Effacer la sélection d'annotation lors du rafraîchissement
        # ... (reste de la méthode update_page_view)
        if not self.current_pdf_document or not (0 <= self.current_page_number < self.current_pdf_document.page_count):
            if self.pdf_scene: self.pdf_scene.clear()
            self.pdf_view_item = QGraphicsPixmapItem();
            if self.pdf_scene: self.pdf_scene.addItem(self.pdf_view_item)
            self.pdf_view_item.setPixmap(QPixmap()); return
        try:
            page = self.current_pdf_document.load_page(self.current_page_number)
            if not page: raise RuntimeError(self.tr("Impossible charger page {0}.").format(self.current_page_number + 1))
            matrix = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor); matrix.preRotate(self.current_view_rotation_angle)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888); pixmap = QPixmap.fromImage(qimage)
            if self.pdf_scene: self.pdf_scene.clear()
            self.pdf_view_item = QGraphicsPixmapItem(pixmap)
            if self.pdf_scene: self.pdf_scene.addItem(self.pdf_view_item); self.pdf_scene.setSceneRect(QRectF(pixmap.rect()))
            if self.search_term and self.current_flat_results_list and 0 <= self.current_search_highlight_idx < len(self.current_flat_results_list):
                page_idx_res, rect_res = self.current_flat_results_list[self.current_search_highlight_idx]
                if page_idx_res == self.current_page_number: self._highlight_search_result_on_scene(rect_res)
        except Exception as e:
            logging.error(self.tr("Erreur affichage page {0}: {1}").format(self.current_page_number + 1, str(e)), exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur d'affichage"), self.tr("Impossible afficher page {0}.\n{1}").format(self.current_page_number + 1, str(e)))
            if self.pdf_scene: self.pdf_scene.clear()

    def update_navigation_controls(self):
        # ... (inchangé)
        if self.current_pdf_document and self.current_pdf_document.page_count > 0:
            num_pages = self.current_pdf_document.page_count
            self.prev_page_button.setEnabled(self.current_page_number > 0); self.next_page_button.setEnabled(self.current_page_number < num_pages - 1)
            self.page_spinbox.blockSignals(True); self.page_spinbox.setRange(1, num_pages); self.page_spinbox.setValue(self.current_page_number + 1)
            self.page_spinbox.setEnabled(True); self.page_spinbox.blockSignals(False); self.total_pages_label.setText(f"/ {num_pages}")
        else: self._disable_all_controls()

    def _disable_all_controls(self):
        # ... (ajouter self.delete_annotation_button.setEnabled(False))
        self.prev_page_button.setEnabled(False); self.next_page_button.setEnabled(False); self.page_spinbox.setEnabled(False)
        self.zoom_in_button.setEnabled(False); self.zoom_out_button.setEnabled(False); self.zoom_original_button.setEnabled(False)
        self.zoom_fit_page_button.setEnabled(False); self.zoom_fit_width_button.setEnabled(False)
        self.rotate_ccw_button.setEnabled(False); self.rotate_cw_button.setEnabled(False)
        self.toggle_annotation_mode_button.setEnabled(False); self.toggle_annotation_mode_button.setChecked(False)
        self.save_annotations_button.setEnabled(False)
        if hasattr(self, 'delete_annotation_button'): self.delete_annotation_button.setEnabled(False)
        if not self.total_pages_label.text().startswith(self.tr("Erreur")): self.total_pages_label.setText(self.tr("/ N/A"))

    def go_to_page(self, page_num_zero_indexed):
        self._clear_selection_feedback() # Effacer la sélection avant de changer de page
        # ... (reste de la méthode go_to_page)
        if self.current_pdf_document and 0 <= page_num_zero_indexed < self.current_pdf_document.page_count:
            if self.current_page_number != page_num_zero_indexed:
                self.current_page_number = page_num_zero_indexed; self.current_view_rotation_angle = 0
            self._clear_search_highlight_and_results_for_page_change(); self.update_page_view()
            self.update_navigation_controls(); self._highlight_current_thumbnail()
        if self.search_term: self._trigger_search_for_current_term_on_page(self.current_page_number, highlight_first=True)

    # ... (Méthodes de zoom, rotation, closeEvent, recherche, miniatures, signets - inchangées) ...
    def go_to_previous_page(self): self.go_to_page(self.current_page_number - 1)
    def go_to_next_page(self): self.go_to_page(self.current_page_number + 1)
    def go_to_page_from_spinbox(self, value): self.go_to_page(value - 1)
    def zoom(self, factor_change):
        new_zoom = self.current_zoom_factor * factor_change; self.current_zoom_factor = max(0.1, min(new_zoom, 5.0))
        self.update_page_view(); self.zoom_original_button.setEnabled(abs(self.current_zoom_factor - 1.0) > 0.01)
    def set_zoom_factor(self, factor):
        self.current_zoom_factor = max(0.1, min(factor, 5.0)); self.update_page_view()
        self.zoom_original_button.setEnabled(abs(self.current_zoom_factor - 1.0) > 0.01)
    def zoom_to_fit_page(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0 or not self.pdf_view.viewport(): return
        page = self.current_pdf_document.load_page(self.current_page_number); page_width, page_height = page.rect.width, page.rect.height
        view_width, view_height = self.pdf_view.viewport().width() - 2, self.pdf_view.viewport().height() - 2
        if page_width == 0 or page_height == 0 or view_width <=0 or view_height <=0 : return
        self.set_zoom_factor(min(view_width / page_width, view_height / page_height))
    def zoom_to_fit_width(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0 or not self.pdf_view.viewport(): return
        page = self.current_pdf_document.load_page(self.current_page_number); page_width = page.rect.width
        view_width = self.pdf_view.viewport().width() - 2
        if page_width == 0 or view_width <= 0: return; self.set_zoom_factor(view_width / page_width)
    def rotate_view(self, angle_degrees):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0: return
        self.current_view_rotation_angle = (self.current_view_rotation_angle + angle_degrees) % 360; self.update_page_view()
    def closeEvent(self, event):
        if self.thumbnail_loader_thread and self.thumbnail_loader_thread.isRunning():
            self.thumbnail_loader_thread.requestInterruption(); self.thumbnail_loader_thread.wait()
        if self.current_pdf_document:
            try: self.current_pdf_document.close()
            except Exception as e: logging.warning(f"Erreur fermeture PDF: {e}")
        super().closeEvent(event)
    def _clear_search_highlight(self):
        if self.search_highlight_item and self.search_highlight_item.scene():
            self.pdf_scene.removeItem(self.search_highlight_item); self.search_highlight_item = None
    def _clear_search_highlight_and_results_for_page_change(self):
        self._clear_search_highlight(); self.current_flat_results_list = []; self.current_search_highlight_idx = -1
        self._update_search_buttons_state(); self.search_results_label.setText("")
    def _reset_full_search_state(self):
        self._clear_search_highlight(); self.search_term = ""; self.all_search_results_map = {}
        self.current_flat_results_list = []; self.current_search_highlight_idx = -1; self.search_input.clear()
        self._update_search_buttons_state(); self.search_results_label.setText("")
    def _on_search_triggered(self):
        new_search_term = self.search_input.text()
        if not new_search_term.strip(): self._reset_full_search_state(); return
        if new_search_term != self.search_term or not self.all_search_results_map:
            self.search_term = new_search_term; self.all_search_results_map = {}; self.current_flat_results_list = []
            self.current_search_highlight_idx = -1
            if not self.current_pdf_document or self.current_pdf_document.page_count == 0: self._update_search_buttons_state(); return
            QApplication.setOverrideCursor(Qt.WaitCursor)
            for page_idx in range(self.current_pdf_document.page_count):
                page_results = self._search_text_on_page(page_idx, self.search_term, self.search_case_sensitive_checkbox.isChecked())
                if page_results: self.all_search_results_map[page_idx] = page_results;
                for rect in page_results: self.current_flat_results_list.append((page_idx, rect))
            QApplication.restoreOverrideCursor()
        if not self.current_flat_results_list:
            self.search_results_label.setText(self.tr("Aucun résultat")); self._clear_search_highlight(); self._update_search_buttons_state(); return
        self.current_search_highlight_idx = 0; self._jump_to_search_result(self.current_search_highlight_idx); self._update_search_buttons_state()
    def _search_text_on_page(self, page_idx, text, case_sensitive):
        if not self.current_pdf_document: return []
        page = self.current_pdf_document.load_page(page_idx); return page.search_for(text.strip(), quads=False)
    def _trigger_search_for_current_term_on_page(self, page_idx, highlight_first=False):
        if not self.search_term or not self.current_pdf_document: return
        page_results = self._search_text_on_page(page_idx, self.search_term, self.search_case_sensitive_checkbox.isChecked())
        self.all_search_results_map[page_idx] = page_results; self.current_flat_results_list = []
        for p_idx, rects in sorted(self.all_search_results_map.items()):
            for r in rects: self.current_flat_results_list.append((p_idx, r))
        if not self.current_flat_results_list:
            self.current_search_highlight_idx = -1; self._clear_search_highlight(); self.search_results_label.setText(self.tr("Aucun résultat"))
        elif highlight_first:
            new_highlight_idx = -1
            for i, (p_idx_res, _) in enumerate(self.current_flat_results_list):
                if p_idx_res == page_idx: new_highlight_idx = i; break
            if new_highlight_idx != -1: self.current_search_highlight_idx = new_highlight_idx; self._jump_to_search_result(self.current_search_highlight_idx, navigate_to_page=False)
            else: self.current_search_highlight_idx = 0; self._jump_to_search_result(self.current_search_highlight_idx)
        self._update_search_buttons_state()
    def _navigate_search_results(self, direction):
        if not self.current_flat_results_list: return
        new_idx = self.current_search_highlight_idx + direction
        if 0 <= new_idx < len(self.current_flat_results_list): self.current_search_highlight_idx = new_idx; self._jump_to_search_result(self.current_search_highlight_idx)
        elif new_idx < 0:
            reply = QMessageBox.question(self, self.tr("Recherche PDF"), self.tr("Premier résultat atteint. Continuer depuis la fin ?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes: self.current_search_highlight_idx = len(self.current_flat_results_list) - 1; self._jump_to_search_result(self.current_search_highlight_idx)
        elif new_idx >= len(self.current_flat_results_list):
            reply = QMessageBox.question(self, self.tr("Recherche PDF"), self.tr("Dernier résultat atteint. Continuer depuis le début ?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes: self.current_search_highlight_idx = 0; self._jump_to_search_result(self.current_search_highlight_idx)
        self._update_search_buttons_state()
    def _jump_to_search_result(self, flat_idx, navigate_to_page=True):
        if not (0 <= flat_idx < len(self.current_flat_results_list)): self._clear_search_highlight(); return
        page_idx, rect = self.current_flat_results_list[flat_idx]
        if navigate_to_page and self.current_page_number != page_idx: self.go_to_page(page_idx)
        if self.current_page_number == page_idx: self._highlight_search_result_on_scene(rect)
        self.search_results_label.setText(self.tr("Résultat {0} sur {1}").format(self.current_search_highlight_idx + 1, len(self.current_flat_results_list)))
    def _highlight_search_result_on_scene(self, rect: fitz.Rect):
        self._clear_search_highlight();
        if not rect: return
        scene_rect = QRectF(rect.x0*self.current_zoom_factor, rect.y0*self.current_zoom_factor, rect.width*self.current_zoom_factor, rect.height*self.current_zoom_factor)
        self.search_highlight_item = QGraphicsRectItem(scene_rect); self.search_highlight_item.setBrush(QColor(255, 255, 0, 100)); self.search_highlight_item.setPen(Qt.NoPen)
        if self.pdf_scene: self.pdf_scene.addItem(self.search_highlight_item)
        if self.pdf_view: self.pdf_view.ensureVisible(self.search_highlight_item, 50, 50)
    def _update_search_buttons_state(self):
        has_results = bool(self.current_flat_results_list)
        self.search_prev_button.setEnabled(has_results and self.current_search_highlight_idx > 0)
        self.search_next_button.setEnabled(has_results and self.current_search_highlight_idx < len(self.current_flat_results_list) - 1)
    def _load_thumbnails(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0: self.thumbnail_list_widget.clear(); return
        if self.thumbnail_loader_thread and self.thumbnail_loader_thread.isRunning(): self.thumbnail_loader_thread.requestInterruption(); self.thumbnail_loader_thread.wait()
        self.thumbnail_list_widget.clear(); loading_item = QListWidgetItem(self.tr("Chargement des miniatures...")); self.thumbnail_list_widget.addItem(loading_item)
        self._thumbnail_items_buffer = [None] * self.current_pdf_document.page_count
        self.thumbnail_loader_thread = ThumbnailLoaderThread(self.pdf_path, self.current_pdf_document.page_count, self)
        self.thumbnail_loader_thread.thumbnailReady.connect(self._add_thumbnail_item); self.thumbnail_loader_thread.finished.connect(self._on_thumbnail_loading_finished)
        self.thumbnail_loader_thread.errorOccurred.connect(self._on_thumbnail_loading_error); self.thumbnail_loader_thread.start()
    def _add_thumbnail_item(self, page_idx, pixmap):
        if not self.thumbnail_list_widget: return
        if self.thumbnail_list_widget.count() == 1 and self.thumbnail_list_widget.item(0).text() == self.tr("Chargement des miniatures..."): self.thumbnail_list_widget.clear()
        item_text = self.tr("Erreur P.{0}").format(page_idx + 1) if pixmap.isNull() else self.tr("Page {0}").format(page_idx + 1)
        item_icon = QIcon() if pixmap.isNull() else QIcon(pixmap)
        item = QListWidgetItem(item_icon, item_text); item.setData(Qt.UserRole, page_idx); item.setSizeHint(QSize(120, 160))
        if 0 <= page_idx < len(self._thumbnail_items_buffer): self._thumbnail_items_buffer[page_idx] = item
        else: self.thumbnail_list_widget.addItem(item)
    def _on_thumbnail_loading_finished(self):
        if self.thumbnail_list_widget.count() == 1 and self.thumbnail_list_widget.item(0).text() == self.tr("Chargement des miniatures..."): self.thumbnail_list_widget.clear()
        for item in self._thumbnail_items_buffer:
            if item: self.thumbnail_list_widget.addItem(item)
        self._thumbnail_items_buffer = []; logging.info(self.tr("Chargement des miniatures terminé.")); self._highlight_current_thumbnail()
    def _on_thumbnail_loading_error(self, error_message):
        logging.error(self.tr("Erreur du thread de chargement des miniatures: {0}").format(error_message))
        if self.thumbnail_list_widget.count() == 1 and self.thumbnail_list_widget.item(0).text() == self.tr("Chargement des miniatures..."):
            self.thumbnail_list_widget.item(0).setText(self.tr("Erreur chargement miniatures"))
        else: QMessageBox.warning(self, self.tr("Erreur Miniatures"), self.tr("Une erreur est survenue lors du chargement des miniatures."))
    def _on_thumbnail_clicked(self, item: QListWidgetItem):
        try: page_idx = item.data(Qt.UserRole);_ = isinstance(page_idx, int) and self.go_to_page(page_idx)
        except Exception as e: logging.error(self.tr("Erreur en cliquant sur la miniature : {0}").format(str(e)), exc_info=True)
    def _highlight_current_thumbnail(self):
        try:
            if not self.thumbnail_list_widget or self.thumbnail_list_widget.count() == 0: return
            if 0 <= self.current_page_number < self.thumbnail_list_widget.count():
                item = self.thumbnail_list_widget.item(self.current_page_number)
                if item: self.thumbnail_list_widget.setCurrentItem(item)
        except Exception as e: logging.error(self.tr("Erreur lors de la mise en évidence de la miniature : {0}").format(str(e)), exc_info=True)
    def _load_bookmarks(self):
        self.bookmark_tree_widget.clear();
        if not self.current_pdf_document: return
        try: toc = self.current_pdf_document.get_toc(simple=False)
        except Exception as e_toc:
            logging.error(self.tr("Erreur TOC: {0}").format(str(e_toc)), exc_info=True)
            self.left_panel_tab_widget.setTabText(1, self.tr("Signets (Erreur)")); QMessageBox.warning(self, self.tr("Erreur Signets"), self.tr("Impossible charger table des matières.")); return
        if not toc: self.left_panel_tab_widget.setTabText(1, self.tr("Signets (Aucun)")); return
        self.left_panel_tab_widget.setTabText(1, self.tr("Signets"))
        def add_toc_items_recursively(parent_item_or_tree, toc_entries_level):
            try:
                for entry in toc_entries_level:
                    level, title, page_num_1_indexed, dest_dict = entry
                    tree_item = QTreeWidgetItem([title if title else self.tr("Sans titre")])
                    tree_item.setData(0, Qt.UserRole, {'page': page_num_1_indexed - 1, 'dest_details': dest_dict})
                    if isinstance(parent_item_or_tree, QTreeWidget): parent_item_or_tree.addTopLevelItem(tree_item)
                    else: parent_item_or_tree.addChild(tree_item)
                    children = []; current_entry_index_in_toc = -1
                    for i, e_loop in enumerate(toc):
                        if e_loop == entry: current_entry_index_in_toc = i; break
                    if current_entry_index_in_toc != -1:
                        for i_loop in range(current_entry_index_in_toc + 1, len(toc)):
                            next_entry_tuple = toc[i_loop]; next_level = next_entry_tuple[0]
                            if next_level == level + 1: children.append(next_entry_tuple)
                            elif next_level <= level: break
                    if children: add_toc_items_recursively(tree_item, children)
            except Exception as e_add_item: logging.error(self.tr("Erreur ajout item signet : {0}").format(str(e_add_item)), exc_info=True)
        try:
            top_level_toc_items = [entry for entry in toc if entry[0] == 1]
            add_toc_items_recursively(self.bookmark_tree_widget, top_level_toc_items)
            self.bookmark_tree_widget.expandAll()
        except Exception as e_build_tree:
            logging.error(self.tr("Erreur construction arbre signets : {0}").format(str(e_build_tree)), exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Signets"), self.tr("Partie table des matières non affichable."))
    def _on_bookmark_clicked(self, item: QTreeWidgetItem, column: int):
        try:
            data = item.data(0, Qt.UserRole)
            if data and isinstance(data, dict) and 'page' in data:
                page_idx_0_based = data['page']; dest_details = data.get('dest_details', {})
                if not (self.current_pdf_document and 0 <= page_idx_0_based < self.current_pdf_document.page_count):
                    logging.warning(self.tr("Signet: page invalide {0}").format(page_idx_0_based)); return
                self.go_to_page(page_idx_0_based)
                QTimer.singleShot(0, lambda: self._apply_bookmark_destination_details(dest_details, page_idx_0_based))
        except Exception as e: logging.error(self.tr("Erreur clic signet : {0}").format(str(e)), exc_info=True)
    def _apply_bookmark_destination_details(self, dest_details: dict, target_page_idx: int):
        try:
            if not self.current_pdf_document or self.current_page_number != target_page_idx: return
            logging.debug(self.tr("Application détails destination signet page {0}: {1}").format(target_page_idx+1, dest_details))
            kind = dest_details.get('kind')
            if kind == fitz.PDF_DEST_FITH: self.zoom_to_fit_width()
            elif kind == fitz.PDF_DEST_FITV:
                page_rect = self.current_pdf_document.load_page(target_page_idx).rect
                if page_rect.height > page_rect.width: self.zoom_to_fit_page()
            elif dest_details.get('zoom', 0) > 0: self.set_zoom_factor(dest_details['zoom'])
            scroll_to_point = dest_details.get('to')
            if scroll_to_point:
                scene_x, scene_y = scroll_to_point.x*self.current_zoom_factor, scroll_to_point.y*self.current_zoom_factor
                if self.pdf_view: self.pdf_view.centerOn(QPointF(scene_x, scene_y))
                logging.debug(self.tr("Signet: Défilement PDF {0}, scène ({1}, {2})").format(scroll_to_point, scene_x, scene_y))
        except Exception as e:
            logging.error(self.tr("Erreur application détails signet : {0}").format(str(e)), exc_info=True)
            QMessageBox.warning(self, self.tr("Navigation Signet"), self.tr("Impossible appliquer détails destination signet."))

    def _on_toggle_annotation_mode(self, checked):
        self.annotation_mode_active = checked
        self._clear_selection_feedback() # Effacer la sélection d'annotation en changeant de mode
        if checked: self.annotation_toolbar.setVisible(True); logging.info(self.tr("Mode annotation activé."))
        else: self.annotation_toolbar.setVisible(False); self._set_annotation_tool(None); logging.info(self.tr("Mode annotation désactivé."))

    def _set_annotation_tool(self, tool_name):
        self._clear_selection_feedback() # Effacer la sélection d'annotation en changeant d'outil
        buttons_tools_map = {"highlighter": self.highlight_tool_button, "ink": self.ink_tool_button, "rectangle": self.rect_tool_button, "circle": self.circle_tool_button}
        for t_name, button in buttons_tools_map.items():
            if button and t_name != tool_name and button.isChecked(): button.setChecked(False)
        if self.current_annotation_tool == tool_name and tool_name is not None:
            self.current_annotation_tool = None # Désactiver -> mode pointeur/selection
            if tool_name in buttons_tools_map and buttons_tools_map[tool_name]: buttons_tools_map[tool_name].setChecked(False)
            self.pdf_view.setCursor(Qt.ArrowCursor); logging.debug(self.tr("Outil annotation désactivé: {0}").format(tool_name))
        elif tool_name is None: # Mode pointeur/selection explicite
            self.current_annotation_tool = None
            for button in buttons_tools_map.values():
                if button and button.isChecked(): button.setChecked(False)
            self.pdf_view.setCursor(Qt.ArrowCursor); logging.debug(self.tr("Mode Pointeur (sélection annotation) activé."))
        else: # Activer un nouvel outil
            self.current_annotation_tool = tool_name; current_button = buttons_tools_map.get(tool_name)
            if current_button and not current_button.isChecked(): current_button.setChecked(True)
            if tool_name in ["highlighter", "rectangle", "circle", "ink"]: self.pdf_view.setCursor(Qt.CrossCursor)
            else: self.pdf_view.setCursor(Qt.ArrowCursor) # Ne devrait pas arriver si tous les outils sont dans la map
            logging.debug(self.tr("Outil annotation activé: {0}").format(self.current_annotation_tool))

    def _choose_stroke_color(self):
        color = QColorDialog.getColor(self.current_stroke_color, self, self.tr("Choisir couleur du trait"))
        if color.isValid(): self.current_stroke_color = color
    def _choose_highlight_color(self):
        color = QColorDialog.getColor(QColor.fromRgbF(self.current_highlight_color.redF(), self.current_highlight_color.greenF(), self.current_highlight_color.blueF()), self, self.tr("Choisir couleur du surlignage"))
        if color.isValid(): self.current_highlight_color = QColor(color.red(), color.green(), color.blue(), 180)
    def _choose_stroke_width(self):
        width, ok = QInputDialog.getDouble(self, self.tr("Épaisseur du trait"), self.tr("Entrez l'épaisseur:"), self.current_stroke_width, 0.5, 10, 1)
        if ok: self.current_stroke_width = width

    def _save_annotated_document(self):
        if not self.current_pdf_document or not self.document_modified_by_annotation:
            logging.info(self.tr("Aucune modification à enregistrer.")); return
        original_path = self.pdf_path; dir_name = os.path.dirname(original_path)
        base_name, ext = os.path.splitext(os.path.basename(original_path)); counter = 0
        default_new_base = f"{base_name}_annotated"; default_new_path_candidate = os.path.join(dir_name, f"{default_new_base}{ext}")
        while os.path.exists(default_new_path_candidate):
            counter += 1; default_new_path_candidate = os.path.join(dir_name, f"{default_new_base}_{counter}{ext}")
        new_file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Enregistrer PDF annoté sous..."), default_new_path_candidate, self.tr("Fichiers PDF (*.pdf)"))
        if new_file_path:
            try:
                self.current_pdf_document.save(new_file_path, garbage=4, deflate=True, incremental=False)
                self.document_modified_by_annotation = False; self.save_annotations_button.setEnabled(False)
                self.documentSavedAsNewVersion.emit(self.pdf_path, new_file_path)
                QMessageBox.information(self, self.tr("Sauvegarde Réussie"), self.tr("Document annoté sauvegardé:\n{0}").format(new_file_path))
                logging.info(self.tr("Document annoté sauvegardé: {0}").format(new_file_path))
            except Exception as e:
                logging.error(self.tr("Erreur sauvegarde PDF annoté : {0}").format(str(e)), exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Sauvegarde"), self.tr("Impossible sauvegarder document annoté.\n{0}").format(str(e)))
        else: logging.info(self.tr("Sauvegarde annulée."))

    def _get_pdf_coordinates_from_scene_rect(self, scene_rect: QRectF) -> fitz.Rect:
        transform_matrix_view = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor); transform_matrix_view.preRotate(self.current_view_rotation_angle)
        inv_transform_matrix = ~transform_matrix_view
        tl_pdf = fitz.Point(scene_rect.topLeft().x(), scene_rect.topLeft().y()) * inv_transform_matrix
        br_pdf = fitz.Point(scene_rect.bottomRight().x(), scene_rect.bottomRight().y()) * inv_transform_matrix
        return fitz.Rect(tl_pdf, br_pdf).normalize()
    def _get_pdf_coordinates_from_scene_points(self, points_scene: list[QPointF]) -> list[fitz.Point]:
        transform_matrix_view = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor); transform_matrix_view.preRotate(self.current_view_rotation_angle)
        inv_transform_matrix = ~transform_matrix_view
        return [fitz.Point(p.x(), p.y()) * inv_transform_matrix for p in points_scene]

    def _apply_permanent_highlight(self, selection_rect_scene: QRectF):
        if not self.current_pdf_document or self.current_page_number < 0 or not self.annotation_mode_active: return
        page = self.current_pdf_document.load_page(self.current_page_number);
        if not page: return
        pdf_rect = self._get_pdf_coordinates_from_scene_rect(selection_rect_scene)
        if pdf_rect.is_empty: logging.warning(self.tr("Sélection surlignage vide.")); return
        try:
            annot = page.add_highlight_annot(pdf_rect)
            if annot:
                rgb_float = (self.current_highlight_color.redF(), self.current_highlight_color.greenF(), self.current_highlight_color.blueF())
                annot.set_colors(stroke=rgb_float); annot.set_opacity(self.current_highlight_color.alphaF())
                annot.update(); self.document_modified_by_annotation = True; self.save_annotations_button.setEnabled(True); self.update_page_view(); logging.info(self.tr("Surlignage permanent ajouté."))
            else: logging.warning(self.tr("Impossible ajouter surlignage."))
        except Exception as e: logging.error(self.tr("Erreur surlignage: {0}").format(str(e)), exc_info=True); QMessageBox.warning(self, self.tr("Erreur annotation"), self.tr("Impossible ajouter surlignage."))
    def _apply_permanent_ink(self, points_scene_list):
        if not self.current_pdf_document or self.current_page_number < 0 or not self.annotation_mode_active or not points_scene_list: return
        page = self.current_pdf_document.load_page(self.current_page_number);
        if not page: return
        points_pdf_list = self._get_pdf_coordinates_from_scene_points(points_scene_list)
        if len(points_pdf_list) < 2: logging.info(self.tr("Tracé dessin trop court.")); return
        try:
            annot = page.add_ink_annot([points_pdf_list])
            if annot:
                rgb_float = (self.current_stroke_color.redF(), self.current_stroke_color.greenF(), self.current_stroke_color.blueF())
                annot.set_colors(stroke=rgb_float); annot.set_border(width=self.current_stroke_width)
                annot.update(); self.document_modified_by_annotation = True; self.save_annotations_button.setEnabled(True); self.update_page_view(); logging.info(self.tr("Dessin libre permanent ajouté."))
            else: logging.warning(self.tr("Impossible ajouter dessin libre."))
        except Exception as e: logging.error(self.tr("Erreur dessin libre: {0}").format(str(e)), exc_info=True); QMessageBox.warning(self, self.tr("Erreur annotation"), self.tr("Impossible ajouter dessin."))
    def _apply_permanent_rectangle(self, selection_rect_scene: QRectF):
        if not self.current_pdf_document or self.current_page_number < 0 or not self.annotation_mode_active: return
        page = self.current_pdf_document.load_page(self.current_page_number);
        if not page: return
        pdf_rect = self._get_pdf_coordinates_from_scene_rect(selection_rect_scene)
        if pdf_rect.is_empty: logging.warning(self.tr("Sélection Rectangle vide.")); return
        try:
            annot = page.add_rect_annot(pdf_rect)
            if annot:
                rgb_float = (self.current_stroke_color.redF(), self.current_stroke_color.greenF(), self.current_stroke_color.blueF())
                annot.set_colors(stroke=rgb_float, fill=None); annot.set_border(width=self.current_stroke_width)
                annot.update(); self.document_modified_by_annotation = True; self.save_annotations_button.setEnabled(True); self.update_page_view()
                logging.info(self.tr("Rectangle permanent ajouté."))
            else: logging.warning(self.tr("Impossible d'ajouter Rectangle."))
        except Exception as e: logging.error(self.tr("Erreur Rectangle: {0}").format(str(e)), exc_info=True); QMessageBox.warning(self, self.tr("Erreur annotation"), self.tr("Impossible d'ajouter Rectangle."))
    def _apply_permanent_circle(self, selection_rect_scene: QRectF):
        if not self.current_pdf_document or self.current_page_number < 0 or not self.annotation_mode_active: return
        page = self.current_pdf_document.load_page(self.current_page_number);
        if not page: return
        pdf_rect = self._get_pdf_coordinates_from_scene_rect(selection_rect_scene)
        if pdf_rect.is_empty: logging.warning(self.tr("Sélection Cercle vide.")); return
        try:
            annot = page.add_circle_annot(pdf_rect)
            if annot:
                rgb_float = (self.current_stroke_color.redF(), self.current_stroke_color.greenF(), self.current_stroke_color.blueF())
                annot.set_colors(stroke=rgb_float, fill=None); annot.set_border(width=self.current_stroke_width)
                annot.update(); self.document_modified_by_annotation = True; self.save_annotations_button.setEnabled(True); self.update_page_view()
                logging.info(self.tr("Cercle permanent ajouté."))
            else: logging.warning(self.tr("Impossible d'ajouter Cercle."))
        except Exception as e: logging.error(self.tr("Erreur Cercle: {0}").format(str(e)), exc_info=True); QMessageBox.warning(self, self.tr("Erreur annotation"), self.tr("Impossible d'ajouter Cercle."))

    def _delete_selected_annotation(self):
        if not self.selected_annotation_object or not self.current_pdf_document or self.current_page_number < 0:
            logging.warning(self.tr("Aucune annotation sélectionnée à supprimer ou document/page invalide."))
            return

        page = self.current_pdf_document.load_page(self.current_page_number)
        if not page:
            logging.error(self.tr("Impossible de charger la page pour supprimer l'annotation."))
            return

        try:
            page.delete_annot(self.selected_annotation_object)
            self.document_modified_by_annotation = True
            self.save_annotations_button.setEnabled(True)
            self._clear_selection_feedback() # Ceci va aussi désactiver le bouton Supprimer
            self.update_page_view()
            logging.info(self.tr("Annotation supprimée avec succès."))
        except Exception as e:
            logging.error(self.tr("Erreur lors de la suppression de l'annotation: {0}").format(str(e)), exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur de Suppression"), self.tr("Impossible de supprimer l'annotation sélectionnée."))


    def graphics_view_mouse_press(self, event: QMouseEvent):
        self.mouse_press_pos_scene = self.pdf_view.mapToScene(event.pos())
        # Effacer la sélection d'annotation précédente si on clique ailleurs ou qu'on commence un nouveau dessin
        if not (self.current_annotation_tool and event.button() == Qt.LeftButton) : # Si on ne commence pas un nouveau dessin
             self._clear_selection_feedback()

        self.current_selection_rect_item = None; self.current_selection_ellipse_item = None; self.current_ink_preview_item = None

        if self.annotation_mode_active and event.button() == Qt.LeftButton:
            current_tool = self.current_annotation_tool
            if current_tool == "highlighter" or current_tool == "rectangle":
                self.current_selection_rect_item = QGraphicsRectItem(QRectF(self.mouse_press_pos_scene, self.mouse_press_pos_scene))
                pen_color = self.current_highlight_color if current_tool == "highlighter" else self.current_stroke_color
                preview_pen_color = QColor(pen_color.red(), pen_color.green(), pen_color.blue(), 150)
                self.current_selection_rect_item.setPen(QPen(preview_pen_color, 1, Qt.DashLine))
                if current_tool == "highlighter": self.current_selection_rect_item.setBrush(QColor(self.current_highlight_color.red(), self.current_highlight_color.green(), self.current_highlight_color.blue(), 70))
                else: self.current_selection_rect_item.setBrush(Qt.NoBrush)
                if self.pdf_scene: self.pdf_scene.addItem(self.current_selection_rect_item)
                event.accept()
            elif current_tool == "circle":
                self.current_selection_ellipse_item = QGraphicsEllipseItem(QRectF(self.mouse_press_pos_scene, self.mouse_press_pos_scene))
                preview_pen_color = QColor(self.current_stroke_color.red(), self.current_stroke_color.green(), self.current_stroke_color.blue(), 150)
                self.current_selection_ellipse_item.setPen(QPen(preview_pen_color, 1, Qt.DashLine))
                self.current_selection_ellipse_item.setBrush(Qt.NoBrush)
                if self.pdf_scene: self.pdf_scene.addItem(self.current_selection_ellipse_item)
                event.accept()
            elif current_tool == "ink":
                self.current_ink_stroke_points_scene = [self.mouse_press_pos_scene]
                path = QPainterPath(self.mouse_press_pos_scene)
                self.current_ink_preview_item = QGraphicsPathItem(path)
                pen = QPen(self.current_stroke_color, self.current_stroke_width * self.current_zoom_factor)
                self.current_ink_preview_item.setPen(pen)
                if self.pdf_scene: self.pdf_scene.addItem(self.current_ink_preview_item)
                event.accept()
            elif current_tool is None: # Mode pointeur/sélection en mode annotation
                if self.current_pdf_document and 0 <= self.current_page_number < self.current_pdf_document.page_count:
                    page = self.current_pdf_document.load_page(self.current_page_number)
                    pdf_point = self._get_pdf_coordinates_from_scene_points([self.mouse_press_pos_scene])[0]

                    found_annot = None
                    for annot in page.annots(): # Itérer en ordre inverse pour sélectionner celle du dessus en cas de superposition
                        if annot.rect.contains(pdf_point):
                            found_annot = annot
                            break # Prendre la première (qui est la dernière ajoutée/plus haute dans l'ordre z)

                    if found_annot:
                        self.selected_annotation_object = found_annot
                        # Afficher le BBox
                        # La transformation du rect de l'annotation vers la scène est la même que pour le surlignage de recherche
                        scene_rect = QRectF(found_annot.rect.x0 * self.current_zoom_factor,
                                            found_annot.rect.y0 * self.current_zoom_factor,
                                            found_annot.rect.width * self.current_zoom_factor,
                                            found_annot.rect.height * self.current_zoom_factor)
                        # TODO: Appliquer la rotation de la VUE au BBox de sélection
                        # Pour l'instant, le BBox ne sera pas rotaté avec la vue.

                        self.selected_annotation_bbox_item = QGraphicsRectItem(scene_rect)
                        self.selected_annotation_bbox_item.setPen(QPen(QColor("cyan"), 2, Qt.DotLine))
                        if self.pdf_scene: self.pdf_scene.addItem(self.selected_annotation_bbox_item)
                        self.delete_annotation_button.setEnabled(True)
                        logging.debug(f"Annotation sélectionnée: {found_annot.type}, rect: {found_annot.rect}")
                        event.accept()
                    else:
                         self._clear_selection_feedback() # Si on clique dans le vide en mode sélection
        else:
             self._clear_selection_feedback() # Si pas en mode annotation, ou clic droit, etc.
             pass

    def graphics_view_mouse_move(self, event: QMouseEvent):
        current_pos_scene = self.pdf_view.mapToScene(event.pos())
        if self.annotation_mode_active and event.buttons() == Qt.LeftButton:
            current_tool = self.current_annotation_tool
            if current_tool in ["highlighter", "rectangle"] and self.current_selection_rect_item:
                self.current_selection_rect_item.setRect(QRectF(self.mouse_press_pos_scene, current_pos_scene).normalized()); event.accept()
            elif current_tool == "circle" and self.current_selection_ellipse_item:
                self.current_selection_ellipse_item.setRect(QRectF(self.mouse_press_pos_scene, current_pos_scene).normalized()); event.accept()
            elif current_tool == "ink" and self.current_ink_preview_item:
                self.current_ink_stroke_points_scene.append(current_pos_scene); path = QPainterPath(self.current_ink_stroke_points_scene[0])
                for point in self.current_ink_stroke_points_scene[1:]: path.lineTo(point)
                self.current_ink_preview_item.setPath(path); event.accept()
        else: pass

    def graphics_view_mouse_release(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.annotation_mode_active :
            current_tool = self.current_annotation_tool
            if current_tool == "highlighter" and self.current_selection_rect_item:
                selection_rect = self.current_selection_rect_item.rect()
                if self.pdf_scene: self.pdf_scene.removeItem(self.current_selection_rect_item); self.current_selection_rect_item = None
                if selection_rect.width() > 3 and selection_rect.height() > 3 : self._apply_permanent_highlight(selection_rect)
                event.accept()
            elif current_tool == "rectangle" and self.current_selection_rect_item:
                selection_rect = self.current_selection_rect_item.rect()
                if self.pdf_scene: self.pdf_scene.removeItem(self.current_selection_rect_item); self.current_selection_rect_item = None
                if selection_rect.width() > 2 and selection_rect.height() > 2: self._apply_permanent_rectangle(selection_rect)
                event.accept()
            elif current_tool == "circle" and self.current_selection_ellipse_item:
                selection_rect = self.current_selection_ellipse_item.rect()
                if self.pdf_scene: self.pdf_scene.removeItem(self.current_selection_ellipse_item); self.current_selection_ellipse_item = None
                if selection_rect.width() > 2 and selection_rect.height() > 2: self._apply_permanent_circle(selection_rect)
                event.accept()
            elif current_tool == "ink" and self.current_ink_preview_item:
                if self.pdf_scene: self.pdf_scene.removeItem(self.current_ink_preview_item); self.current_ink_preview_item = None
                if len(self.current_ink_stroke_points_scene) > 1: self._apply_permanent_ink(self.current_ink_stroke_points_scene)
                self.current_ink_stroke_points_scene = []; event.accept()
            # Pas de `else` ici car si current_tool est None, on est en mode sélection, géré par mousePress.
            # Les nettoyages des items de prévisualisation sont faits au début de mousePress ou si un outil est explicitement désactivé.
        else: # Clic autre que gauche, ou pas en mode annotation
            # Nettoyage général au cas où un item de prévisualisation serait resté
            if self.current_selection_rect_item:
                if self.pdf_scene: self.pdf_scene.removeItem(self.current_selection_rect_item); self.current_selection_rect_item = None
            if self.current_selection_ellipse_item:
                 if self.pdf_scene: self.pdf_scene.removeItem(self.current_selection_ellipse_item); self.current_selection_ellipse_item = None
            if self.current_ink_preview_item:
                if self.pdf_scene: self.pdf_scene.removeItem(self.current_ink_preview_item); self.current_ink_preview_item = None
            pass
        self.mouse_press_pos_scene = None

# --- Thread pour le chargement asynchrone des miniatures ---
# ... (le reste du fichier à partir de la définition de ThumbnailLoaderThread)
class ThumbnailLoaderThread(QThread):
    thumbnailReady = pyqtSignal(int, QPixmap)
    finished = pyqtSignal()
    errorOccurred = pyqtSignal(str)
    def __init__(self, pdf_path, page_count, parent=None): super().__init__(parent); self.pdf_path = pdf_path; self.page_count = page_count
    def run(self):
        doc = None
        try:
            doc = fitz.open(self.pdf_path)
            if doc.page_count != self.page_count:
                logging.warning(QCoreApplication.translate("ThumbnailLoaderThread", "Nb pages changé; arrêt miniatures."))
                self.errorOccurred.emit(QCoreApplication.translate("ThumbnailLoaderThread", "Incohérence nb pages."))
                return
            for page_idx in range(self.page_count):
                if self.isInterruptionRequested(): logging.info(QCoreApplication.translate("ThumbnailLoaderThread", "Chargement miniatures interrompu.")); return
                try:
                    page = doc.load_page(page_idx)
                    if not page: logging.warning(QCoreApplication.translate("ThumbnailLoaderThread", "Impossible charger page {0} pour miniature.").format(page_idx + 1)); continue
                    thumb_matrix = fitz.Matrix(0.15, 0.15); pix = page.get_pixmap(matrix=thumb_matrix, alpha=False)
                    qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888); pixmap = QPixmap.fromImage(qimage)
                    self.thumbnailReady.emit(page_idx, pixmap)
                except Exception as e_page:
                    logging.error(QCoreApplication.translate("ThumbnailLoaderThread", "Erreur miniature page {0}: {1}").format(page_idx + 1, str(e_page)), exc_info=True)
                    self.thumbnailReady.emit(page_idx, QPixmap())
        except Exception as e_doc:
            logging.error(QCoreApplication.translate("ThumbnailLoaderThread", "Erreur ouverture PDF dans thread: {0}").format(str(e_doc)), exc_info=True); self.errorOccurred.emit(str(e_doc))
        finally:
            if doc:
                try: doc.close()
                except Exception as e_close: logging.warning(QCoreApplication.translate("ThumbnailLoaderThread", "Erreur fermeture PDF thread: {0}").format(e_close))
            self.finished.emit()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    test_pdf_path, _ = QFileDialog.getOpenFileName(None, "Select PDF to Test Viewer", "", "PDF Files (*.pdf)")
    if test_pdf_path: viewer = PdfViewerWidget(test_pdf_path); viewer.show(); sys.exit(app.exec_())
    else: sys.exit(0)

# [end of gui/widgets/pdf_viewer_widget.py]
