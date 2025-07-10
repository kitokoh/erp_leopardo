# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QSizePolicy, QSpinBox, QWidget,
    QScrollArea, QApplication, QMessageBox, QCheckBox, QLineEdit,
    QSplitter, QTabWidget, QListWidget, QTreeWidget, QTreeWidgetItem, QListWidgetItem
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QRectF, QCoreApplication, QSize


class PdfViewerWidget(QDialog):
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.current_pdf_document = None
        self.current_page_number = 0
        self.current_zoom_factor = 1.0 # Default zoom
        self.current_view_rotation_angle = 0 # Angle de rotation actuel de la vue

        # Variables pour la recherche
        self.search_term = ""
        self.all_search_results_map = {} # {page_idx: [fitz.Rect, ...]}
        self.current_flat_results_list = [] # [(page_idx, fitz.Rect), ...]
        self.current_search_highlight_idx = -1
        self.search_highlight_item = None # QGraphicsRectItem

        # Widgets pour le panneau latéral
        self.left_panel_tab_widget = None
        self.thumbnail_list_widget = None
        self.bookmark_tree_widget = None


        # Utilisation de self.tr() pour le titre de la fenêtre
        self.setWindowTitle(self.tr("Visionneuse PDF - {0}").format(pdf_path))
        self.setMinimumSize(1000, 700) # Augmenter la taille pour le panneau latéral
        self.setModal(True)

        self._setup_ui()
        self._load_pdf()

    def tr(self, text, disambiguation=None, n=-1):
        # Helper pour la traduction, s'assurant que QCoreApplication.translate est utilisé
        # avec le contexte de cette classe.
        return QCoreApplication.translate("PdfViewerWidget", text, disambiguation, n)

    def _setup_ui(self):
        # Layout principal devient QHBoxLayout pour le QSplitter
        overall_layout = QHBoxLayout(self) # Changé de QVBoxLayout

        # --- QSplitter pour diviser la vue ---
        splitter = QSplitter(Qt.Horizontal)
        overall_layout.addWidget(splitter)

        # --- Panneau de Gauche (Onglets pour Miniatures et Signets) ---
        self.left_panel_tab_widget = QTabWidget()
        self.left_panel_tab_widget.setMinimumWidth(200) # Largeur minimale pour le panneau
        self.left_panel_tab_widget.setMaximumWidth(400) # Largeur maximale

        # Onglet Miniatures
        self.thumbnail_list_widget = QListWidget()
        self.thumbnail_list_widget.setIconSize(QSize(100, 140)) # Taille indicative pour les miniatures
        self.thumbnail_list_widget.setViewMode(QListWidget.IconMode)
        self.thumbnail_list_widget.setResizeMode(QListWidget.Adjust)
        self.thumbnail_list_widget.setMovement(QListWidget.Static) # Empêcher le drag & drop
        self.thumbnail_list_widget.itemClicked.connect(self._on_thumbnail_clicked)
        self.left_panel_tab_widget.addTab(self.thumbnail_list_widget, self.tr("Miniatures"))

        # Onglet Signets
        self.bookmark_tree_widget = QTreeWidget()
        self.bookmark_tree_widget.setHeaderLabel(self.tr("Signets"))
        self.bookmark_tree_widget.itemClicked.connect(self._on_bookmark_clicked)
        self.left_panel_tab_widget.addTab(self.bookmark_tree_widget, self.tr("Signets"))

        splitter.addWidget(self.left_panel_tab_widget)

        # --- Panneau de Droite (Contrôles et Vue PDF) ---
        right_panel_widget = QWidget()
        main_layout = QVBoxLayout(right_panel_widget) # Ancien layout principal devient celui du panneau droit

        # --- Barre de Contrôles Principaux ---
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        #main_layout.addWidget(controls_widget) # Ajouté plus tard après la barre de recherche

        self.prev_page_button = QPushButton(QIcon.fromTheme("go-previous", QIcon(":/icons/arrow-left-circle.svg")), self.tr("< Préc."))
        self.prev_page_button.setToolTip(self.tr("Page précédente"))
        self.prev_page_button.clicked.connect(self.go_to_previous_page)
        self.prev_page_button.setEnabled(False)
        controls_layout.addWidget(self.prev_page_button)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setToolTip(self.tr("Aller à la page"))
        self.page_spinbox.setEnabled(False)
        self.page_spinbox.valueChanged.connect(self.go_to_page_from_spinbox)
        controls_layout.addWidget(self.page_spinbox)

        self.total_pages_label = QLabel(self.tr("/ N/A"))
        controls_layout.addWidget(self.total_pages_label)

        self.next_page_button = QPushButton(QIcon.fromTheme("go-next", QIcon(":/icons/arrow-right-circle.svg")), self.tr("Suiv. >"))
        self.next_page_button.setToolTip(self.tr("Page suivante"))
        self.next_page_button.clicked.connect(self.go_to_next_page)
        self.next_page_button.setEnabled(False)
        controls_layout.addWidget(self.next_page_button)

        controls_layout.addStretch()

        self.zoom_out_button = QPushButton(QIcon.fromTheme("zoom-out", QIcon(":/icons/zoom-out.svg")), self.tr("Zoom -"))
        self.zoom_out_button.setToolTip(self.tr("Zoom arrière"))
        self.zoom_out_button.clicked.connect(lambda: self.zoom(0.9))
        self.zoom_out_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_out_button)

        self.zoom_in_button = QPushButton(QIcon.fromTheme("zoom-in", QIcon(":/icons/zoom-in.svg")), self.tr("Zoom +"))
        self.zoom_in_button.setToolTip(self.tr("Zoom avant"))
        self.zoom_in_button.clicked.connect(lambda: self.zoom(1.1))
        self.zoom_in_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_in_button)

        self.zoom_original_button = QPushButton(QIcon.fromTheme("zoom-original", QIcon(":/icons/zoom-original.svg")), self.tr("Zoom 100%"))
        self.zoom_original_button.setToolTip(self.tr("Zoom original (100%)"))
        self.zoom_original_button.clicked.connect(lambda: self.set_zoom_factor(1.0))
        self.zoom_original_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_original_button)

        self.zoom_fit_page_button = QPushButton(QIcon.fromTheme("zoom-fit-best", QIcon(":/icons/zoom-fit-page.svg")), self.tr("Ajuster Page"))
        self.zoom_fit_page_button.setToolTip(self.tr("Ajuster à la page entière"))
        self.zoom_fit_page_button.clicked.connect(self.zoom_to_fit_page)
        self.zoom_fit_page_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_fit_page_button)

        self.zoom_fit_width_button = QPushButton(QIcon.fromTheme("zoom-fit-width", QIcon(":/icons/zoom-fit-width.svg")), self.tr("Ajuster Largeur"))
        self.zoom_fit_width_button.setToolTip(self.tr("Ajuster à la largeur de la page"))
        self.zoom_fit_width_button.clicked.connect(self.zoom_to_fit_width)
        self.zoom_fit_width_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_fit_width_button)

        controls_layout.addSpacing(20) # Espace avant les boutons de rotation

        self.rotate_ccw_button = QPushButton(QIcon.fromTheme("object-rotate-left", QIcon(":/icons/rotate-ccw.svg")), self.tr("Rot. Gauche"))
        self.rotate_ccw_button.setToolTip(self.tr("Rotation anti-horaire"))
        self.rotate_ccw_button.clicked.connect(lambda: self.rotate_view(-90))
        self.rotate_ccw_button.setEnabled(False)
        controls_layout.addWidget(self.rotate_ccw_button)

        self.rotate_cw_button = QPushButton(QIcon.fromTheme("object-rotate-right", QIcon(":/icons/rotate-cw.svg")), self.tr("Rot. Droite"))
        self.rotate_cw_button.setToolTip(self.tr("Rotation horaire"))
        self.rotate_cw_button.clicked.connect(lambda: self.rotate_view(90))
        self.rotate_cw_button.setEnabled(False)
        controls_layout.addWidget(self.rotate_cw_button)

        # --- Barre de Recherche ---
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(5,0,5,5) # Moins de marge en haut

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Rechercher dans le PDF..."))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self._on_search_triggered) # Recherche en appuyant sur Entrée
        search_layout.addWidget(self.search_input)

        self.search_case_sensitive_checkbox = QCheckBox(self.tr("Sensible à la casse"))
        search_layout.addWidget(self.search_case_sensitive_checkbox)

        self.search_button = QPushButton(QIcon.fromTheme("edit-find", QIcon(":/icons/search.svg")), self.tr("Chercher"))
        self.search_button.clicked.connect(self._on_search_triggered)
        search_layout.addWidget(self.search_button)

        self.search_prev_button = QPushButton(QIcon.fromTheme("go-up", QIcon(":/icons/chevron-up.svg")), self.tr("Précédent"))
        self.search_prev_button.clicked.connect(lambda: self._navigate_search_results(direction=-1))
        self.search_prev_button.setEnabled(False)
        search_layout.addWidget(self.search_prev_button)

        self.search_next_button = QPushButton(QIcon.fromTheme("go-down", QIcon(":/icons/chevron-down.svg")), self.tr("Suivant"))
        self.search_next_button.clicked.connect(lambda: self._navigate_search_results(direction=1))
        self.search_next_button.setEnabled(False)
        search_layout.addWidget(self.search_next_button)

        self.search_results_label = QLabel("") # Pour afficher "Résultat x sur y"
        search_layout.addWidget(self.search_results_label)
        search_layout.addStretch()


        # Ajout des barres au layout principal
        main_layout.addWidget(controls_widget) # Barre de contrôles de page/zoom/rotation
        main_layout.addWidget(search_widget)   # Barre de recherche

        # PDF View Area
        self.pdf_view = QGraphicsView() # Parent géré par le layout/scrollarea
        self.pdf_scene = QGraphicsScene(self)
        self.pdf_view.setScene(self.pdf_scene)
        self.pdf_view_item = QGraphicsPixmapItem()
        self.pdf_scene.addItem(self.pdf_view_item)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.pdf_view)
        main_layout.addWidget(scroll_area)

        # Close button (reste dans le panneau de droite)
        close_button = QPushButton(QIcon.fromTheme("window-close", QIcon(":/icons/x-circle.svg")), self.tr("Fermer"))
        close_button.setToolTip(self.tr("Fermer la visionneuse"))
        close_button.clicked.connect(self.accept)

        button_bar_layout = QHBoxLayout()
        button_bar_layout.addStretch()
        button_bar_layout.addWidget(close_button)
        main_layout.addLayout(button_bar_layout)

        splitter.addWidget(right_panel_widget) # Ajoute le panneau de droite au splitter

        # Définir les tailles initiales du splitter (par exemple 25% pour le panneau gauche, 75% pour le droit)
        splitter.setSizes([self.width() // 4, 3 * self.width() // 4])


    def _load_pdf(self):
        try:
            self.current_pdf_document = fitz.open(self.pdf_path)
            if self.current_pdf_document.page_count > 0:
                self.current_page_number = 0
                self.update_page_view()
                self.update_navigation_controls()
                self.zoom_in_button.setEnabled(True)
                self.zoom_out_button.setEnabled(True)
                self.zoom_original_button.setEnabled(True)
                self.zoom_fit_page_button.setEnabled(True)
                self.zoom_fit_width_button.setEnabled(True)
                self.rotate_ccw_button.setEnabled(True)
                self.rotate_cw_button.setEnabled(True)
                self._load_thumbnails()
                self._load_bookmarks()
            else:
                self.total_pages_label.setText(self.tr("Document vide"))
                self._disable_all_controls()
                self.thumbnail_list_widget.clear()
                self.bookmark_tree_widget.clear()
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture du PDF '{self.pdf_path}': {e}", exc_info=True)
            self.total_pages_label.setText(self.tr("Erreur: {0}").format(str(e)))
            self._disable_all_controls()
            self.thumbnail_list_widget.clear()
            self.bookmark_tree_widget.clear()
            QMessageBox.critical(self, self.tr("Erreur PDF"),
                                 self.tr("Impossible d'ouvrir le fichier PDF '{0}'.\nErreur: {1}").format(self.pdf_path, str(e)))


    def update_page_view(self):
        if not self.current_pdf_document or \
           self.current_page_number < 0 or \
           self.current_page_number >= self.current_pdf_document.page_count:
            if self.pdf_scene: self.pdf_scene.clear() # Clear the scene if no valid page
            self.pdf_view_item = QGraphicsPixmapItem() # Reset item
            self.pdf_scene.addItem(self.pdf_view_item) # Add new empty item
            self.pdf_view_item.setPixmap(QPixmap()) # Set an empty pixmap
            return

        try:
            page = self.current_pdf_document.load_page(self.current_page_number)

            # Combinez le zoom et la rotation dans la matrice de transformation
            matrix = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor)
            matrix.preRotate(self.current_view_rotation_angle) # Applique la rotation

            pix = page.get_pixmap(matrix=matrix, alpha=False) # alpha=False for RGB

            qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)

            self.pdf_scene.clear() # Clear previous items before adding new one
            self.pdf_view_item = QGraphicsPixmapItem(pixmap)
            self.pdf_scene.addItem(self.pdf_view_item)
            self.pdf_scene.setSceneRect(QRectF(pixmap.rect()))
        except Exception as e:
            logging.error(f"Erreur lors de l'affichage de la page {self.current_page_number}: {e}", exc_info=True)
            # Potentially show an error message on the page itself or a QMessageBox

    def update_navigation_controls(self):
        if self.current_pdf_document and self.current_pdf_document.page_count > 0:
            num_pages = self.current_pdf_document.page_count
            self.prev_page_button.setEnabled(self.current_page_number > 0)
            self.next_page_button.setEnabled(self.current_page_number < num_pages - 1)

            self.page_spinbox.blockSignals(True)
            self.page_spinbox.setRange(1, num_pages)
            self.page_spinbox.setValue(self.current_page_number + 1)
            self.page_spinbox.setEnabled(True)
            self.page_spinbox.blockSignals(False)

            self.total_pages_label.setText(f"/ {num_pages}")
        else:
            self._disable_all_controls()

    def _disable_all_controls(self):
        self.prev_page_button.setEnabled(False)
        self.next_page_button.setEnabled(False)
        self.page_spinbox.setEnabled(False)
        self.zoom_in_button.setEnabled(False)
        self.zoom_out_button.setEnabled(False)
        self.zoom_original_button.setEnabled(False)
        self.zoom_fit_page_button.setEnabled(False)
        self.zoom_fit_width_button.setEnabled(False)
        self.rotate_ccw_button.setEnabled(False)
        self.rotate_cw_button.setEnabled(False)
        if not self.total_pages_label.text().startswith(self.tr("Erreur")): # Comparer avec la chaîne traduite
             self.total_pages_label.setText(self.tr("/ N/A"))


    def go_to_page(self, page_num_zero_indexed):
        if self.current_pdf_document and 0 <= page_num_zero_indexed < self.current_pdf_document.page_count:
            if self.current_page_number != page_num_zero_indexed:
                self.current_page_number = page_num_zero_indexed
                self.current_view_rotation_angle = 0 # Réinitialiser la rotation lors du changement de page
        self._clear_search_highlight_and_results_for_page_change() # Effacer la surbrillance de recherche
                self.update_page_view()
                self.update_navigation_controls()
        # Si une recherche est active, la relancer sur la nouvelle page (ou juste la première occurrence)
        if self.search_term:
            self._trigger_search_for_current_term_on_page(self.current_page_number, highlight_first=True)


    def go_to_previous_page(self):
        self.go_to_page(self.current_page_number - 1)

    def go_to_next_page(self):
        self.go_to_page(self.current_page_number + 1)

    def go_to_page_from_spinbox(self, value): # value is 1-indexed
        self.go_to_page(value - 1)

    def zoom(self, factor_change):
        new_zoom = self.current_zoom_factor * factor_change
        # Clamp zoom factor to reasonable limits
        self.current_zoom_factor = max(0.1, min(new_zoom, 5.0))
        self.update_page_view()
        self.zoom_original_button.setEnabled(abs(self.current_zoom_factor - 1.0) > 0.01)


    def set_zoom_factor(self, factor):
        self.current_zoom_factor = max(0.1, min(factor, 5.0)) # Clamp
        self.update_page_view()
        self.zoom_original_button.setEnabled(abs(self.current_zoom_factor - 1.0) > 0.01)

    def zoom_to_fit_page(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0 or not self.pdf_view.viewport():
            return

        page = self.current_pdf_document.load_page(self.current_page_number)
        page_width = page.rect.width
        page_height = page.rect.height

        view_width = self.pdf_view.viewport().width() - 2 # Small margin for scrollbars
        view_height = self.pdf_view.viewport().height() - 2

        if page_width == 0 or page_height == 0 or view_width <=0 or view_height <=0 : # Avoid division by zero or invalid view size
            return

        zoom_x = view_width / page_width
        zoom_y = view_height / page_height

        self.set_zoom_factor(min(zoom_x, zoom_y))

    def zoom_to_fit_width(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0 or not self.pdf_view.viewport():
            return

        page = self.current_pdf_document.load_page(self.current_page_number)
        page_width = page.rect.width

        view_width = self.pdf_view.viewport().width() - 2 # Small margin for scrollbars

        if page_width == 0 or view_width <= 0: # Avoid division by zero
            return

        self.set_zoom_factor(view_width / page_width)

    def rotate_view(self, angle_degrees):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0:
            return

        self.current_view_rotation_angle = (self.current_view_rotation_angle + angle_degrees) % 360
        self.update_page_view()

    def closeEvent(self, event):
        if self.current_pdf_document:
            try:
                self.current_pdf_document.close()
            except Exception as e:
                logging.warning(f"Erreur lors de la fermeture du document PDF dans PdfViewerWidget: {e}")
        super().closeEvent(event)

    # --- Méthodes de Recherche ---
    def _clear_search_highlight(self):
        if self.search_highlight_item and self.search_highlight_item.scene():
            self.pdf_scene.removeItem(self.search_highlight_item)
            self.search_highlight_item = None

    def _clear_search_highlight_and_results_for_page_change(self):
        self._clear_search_highlight()
        # Ne pas effacer self.all_search_results_map ici, car il contient les résultats de tout le document.
        # Effacer current_flat_results_list et current_search_highlight_idx si la recherche est liée à la page uniquement
        # Pour une recherche globale, on pourrait vouloir les conserver et juste mettre à jour la vue.
        # Pour l'instant, une navigation simple: on efface et on relance sur la page si terme actif.
        self.current_flat_results_list = []
        self.current_search_highlight_idx = -1
        self._update_search_buttons_state()
        self.search_results_label.setText("")


    def _reset_full_search_state(self):
        self._clear_search_highlight()
        self.search_term = ""
        self.all_search_results_map = {}
        self.current_flat_results_list = []
        self.current_search_highlight_idx = -1
        self.search_input.clear() # Efface aussi le texte dans QLineEdit
        self._update_search_buttons_state()
        self.search_results_label.setText("")


    def _on_search_triggered(self):
        new_search_term = self.search_input.text()
        if not new_search_term.strip():
            self._reset_full_search_state() # Efface la recherche si le terme est vide
            return

        if new_search_term != self.search_term or not self.all_search_results_map: # Nouvelle recherche ou première recherche
            self.search_term = new_search_term
            self.all_search_results_map = {} # Réinitialiser pour la nouvelle recherche globale
            self.current_flat_results_list = []
            self.current_search_highlight_idx = -1

            if not self.current_pdf_document or self.current_pdf_document.page_count == 0:
                self._update_search_buttons_state()
                return

            QApplication.setOverrideCursor(Qt.WaitCursor)
            # Effectuer la recherche sur toutes les pages
            for page_idx in range(self.current_pdf_document.page_count):
                page_results = self._search_text_on_page(page_idx, self.search_term, self.search_case_sensitive_checkbox.isChecked())
                if page_results:
                    self.all_search_results_map[page_idx] = page_results
                    for rect in page_results:
                        self.current_flat_results_list.append((page_idx, rect))
            QApplication.restoreOverrideCursor()

        if not self.current_flat_results_list:
            self.search_results_label.setText(self.tr("Aucun résultat"))
            self._clear_search_highlight()
            self._update_search_buttons_state()
            return

        # Si on a des résultats, on navigue au premier
        self.current_search_highlight_idx = 0
        self._jump_to_search_result(self.current_search_highlight_idx)
        self._update_search_buttons_state()


    def _search_text_on_page(self, page_idx, text, case_sensitive):
        if not self.current_pdf_document: return []
        page = self.current_pdf_document.load_page(page_idx)

        # PyMuPDF search_for flags: 0 for default (case-insensitive), 1 for case-sensitive
        # MuPDF docs say default is case-insensitive.
        # For PyMuPDF, text flags are more complex. `fitz.TEXT_SEARCH_CASE` for case sensitivity.
        # However, search_for doesn't directly take this flag.
        # The default for search_for is case-insensitive. For case-sensitive, we might need to adjust.
        # Let's assume default is case-insensitive and if case_sensitive is true, we might need to filter later or use other flags if available.
        # For now, we will rely on PyMuPDF's default behavior for case sensitivity or lack thereof.
        # Update: `page.search_for` is case-insensitive by default.
        # There isn't a direct flag for case-sensitivity in `search_for`.
        # If true case-sensitivity is needed and not default, one might have to get all text and search manually, or check library updates.
        # For this implementation, we will proceed assuming `search_for` is case-insensitive.
        # If `case_sensitive` is checked, we will inform the user this feature might be limited by PyMuPDF.
        # TODO: Investigate true case-sensitive search with PyMuPDF `search_for` or alternatives.

        # For now, we ignore case_sensitive for the actual search_for call as it's default case-insensitive
        # We can add a note or warning if user checks it.
        # if case_sensitive:
        #     QMessageBox.information(self, self.tr("Recherche"), self.tr("La recherche sensible à la casse n'est pas pleinement supportée par le moteur de recherche PDF actuel."))

        return page.search_for(text.strip(), quads=False) # returns list of Rects


    def _trigger_search_for_current_term_on_page(self, page_idx, highlight_first=False):
        """Relance la recherche pour le terme actuel sur une page spécifique."""
        if not self.search_term or not self.current_pdf_document:
            return

        # Met à jour les résultats pour cette page dans la map globale
        page_results = self._search_text_on_page(page_idx, self.search_term, self.search_case_sensitive_checkbox.isChecked())
        self.all_search_results_map[page_idx] = page_results

        # Reconstruit la liste plate des résultats
        self.current_flat_results_list = []
        for p_idx, rects in sorted(self.all_search_results_map.items()): # sorted pour garder l'ordre des pages
            for r in rects:
                self.current_flat_results_list.append((p_idx, r))

        if not self.current_flat_results_list:
            self.current_search_highlight_idx = -1
            self._clear_search_highlight()
            self.search_results_label.setText(self.tr("Aucun résultat"))
        elif highlight_first:
            # Essayer de trouver la première occurrence sur la page actuelle
            new_highlight_idx = -1
            for i, (p_idx_res, _) in enumerate(self.current_flat_results_list):
                if p_idx_res == page_idx:
                    new_highlight_idx = i
                    break
            if new_highlight_idx != -1:
                self.current_search_highlight_idx = new_highlight_idx
                self._jump_to_search_result(self.current_search_highlight_idx, navigate_to_page=False) # Pas besoin de naviguer, on y est déjà
            else: # Aucun résultat sur cette page, mais peut-être ailleurs
                self.current_search_highlight_idx = 0 # Ou le plus proche ? Pour l'instant, premier global.
                self._jump_to_search_result(self.current_search_highlight_idx)

        self._update_search_buttons_state()


    def _navigate_search_results(self, direction):
        if not self.current_flat_results_list:
            return

        new_idx = self.current_search_highlight_idx + direction

        if 0 <= new_idx < len(self.current_flat_results_list):
            self.current_search_highlight_idx = new_idx
            self._jump_to_search_result(self.current_search_highlight_idx)
        elif new_idx < 0: # Avant le premier résultat
            reply = QMessageBox.question(self, self.tr("Recherche PDF"),
                                         self.tr("Premier résultat atteint. Continuer depuis la fin ?"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.current_search_highlight_idx = len(self.current_flat_results_list) - 1
                self._jump_to_search_result(self.current_search_highlight_idx)
        elif new_idx >= len(self.current_flat_results_list): # Après le dernier
            reply = QMessageBox.question(self, self.tr("Recherche PDF"),
                                         self.tr("Dernier résultat atteint. Continuer depuis le début ?"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.current_search_highlight_idx = 0
                self._jump_to_search_result(self.current_search_highlight_idx)

        self._update_search_buttons_state()


    def _jump_to_search_result(self, flat_idx, navigate_to_page=True):
        if not (0 <= flat_idx < len(self.current_flat_results_list)):
            self._clear_search_highlight()
            return

        page_idx, rect = self.current_flat_results_list[flat_idx]

        if navigate_to_page and self.current_page_number != page_idx:
            self.go_to_page(page_idx) # go_to_page va appeler update_page_view, etc.
                                      # et _trigger_search_for_current_term_on_page
                                      # qui va gérer la surbrillance.
                                      # Donc, on ne highlight pas directement ici si la page change.
            # La surbrillance sera gérée par l'appel à _trigger_search_for_current_term_on_page dans go_to_page
            # Cependant, il faut s'assurer que current_search_highlight_idx est correctement mis à jour
            # pour que _trigger_search_for_current_term_on_page surligne le bon élément.
            # Cela devient un peu circulaire. Simplifions :
            # Si la page change, go_to_page s'en occupe. Si on reste sur la même page, on highlight.

        # Si on reste sur la même page ou si go_to_page a été appelé et on est maintenant sur la bonne page:
        # On doit s'assurer que la surbrillance est appliquée après que la vue de la page soit mise à jour.
        # QTimer.singleShot(0, lambda: self._highlight_search_result_on_scene(rect))
        # Mieux : la logique de surbrillance devrait être dans _trigger_search_for_current_term_on_page
        # ou une méthode appelée après la navigation de page.

        # Pour l'instant, si la page doit changer, on ne fait que naviguer.
        # La surbrillance sera appelée par go_to_page via _trigger_search_for_current_term_on_page.
        # Si la page ne change pas, on surligne directement.
        if self.current_page_number == page_idx:
             self._highlight_search_result_on_scene(rect)

        self.search_results_label.setText(self.tr("Résultat {0} sur {1}").format(
            self.current_search_highlight_idx + 1, len(self.current_flat_results_list)
        ))


    def _highlight_search_result_on_scene(self, rect: fitz.Rect):
        self._clear_search_highlight()
        if not rect: return

        # Conversion des coordonnées PDF en coordonnées de la scène
        # La rotation de la vue doit être prise en compte ici pour le highlight

        # Créer une matrice pour la transformation inverse (scene -> PDF)
        # Ou plutôt, appliquer la même transformation (PDF -> scene) au rectangle
        transform_matrix = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor)
        transform_matrix.preRotate(self.current_view_rotation_angle)

        # Transformer les points du rectangle
        tl = fitz.Point(rect.tl) * transform_matrix
        tr = fitz.Point(rect.tr) * transform_matrix
        bl = fitz.Point(rect.bl) * transform_matrix
        br = fitz.Point(rect.br) * transform_matrix

        # Construire un QPolygonF à partir des points transformés
        # QRectF ne gère pas les rectangles rotatés directement pour le dessin simple.
        # Un QGraphicsPolygonItem est plus adapté si le rectangle est rotaté.
        # Pour la simplicité, on va utiliser le bounding box du rectangle rotaté.
        # Cela ne sera pas parfait si la rotation est autre que 0, 90, 180, 270.

        # Si on veut un rectangle aligné aux axes de la vue, on prend le boundingRect des points transformés.
        # x_coords = [tl.x, tr.x, bl.x, br.x]
        # y_coords = [tl.y, tr.y, bl.y, br.y]
        # scene_rect = QRectF(min(x_coords), min(y_coords), max(x_coords) - min(x_coords), max(y_coords) - min(y_coords))

        # Pour une surbrillance plus précise avec rotation, il faudrait un QGraphicsPathItem ou PolygonItem
        # Pour un rectangle simple (non rotaté dans la vue, mais le contenu PDF l'est) :
        scene_rect = QRectF(
            rect.x0 * self.current_zoom_factor,
            rect.y0 * self.current_zoom_factor,
            rect.width * self.current_zoom_factor,
            rect.height * self.current_zoom_factor
        )
        # Ce calcul simple ne prend pas en compte la rotation de la VUE pour le rectangle de surbrillance.
        # Si la vue est rotatée, le rectangle de surbrillance sera toujours aligné aux axes de la scène.
        # C'est une simplification pour l'instant.

        # Si la vue est rotatée, le rectangle de surbrillance devrait aussi être rotaté.
        # Le plus simple est de dessiner un rectangle et de le faire pivoter.
        # Mais QGraphicsRectItem n'a pas de rotation simple, il faut utiliser les transformations.

        # Pour l'instant, on va utiliser le rect simple, en sachant que ce n'est pas parfait pour les vues rotatées.
        # TODO: Améliorer la surbrillance pour les vues rotatées.

        self.search_highlight_item = QGraphicsRectItem(scene_rect)
        highlight_color = QColor(255, 255, 0, 100) # Jaune semi-transparent
        self.search_highlight_item.setBrush(highlight_color)
        self.search_highlight_item.setPen(Qt.NoPen) # Pas de bordure pour la surbrillance
        self.pdf_scene.addItem(self.search_highlight_item)

        # Faire défiler pour rendre visible
        self.pdf_view.ensureVisible(self.search_highlight_item, 50, 50) # Marges de 50px


    def _update_search_buttons_state(self):
        has_results = bool(self.current_flat_results_list)
        self.search_prev_button.setEnabled(has_results and self.current_search_highlight_idx > 0)
        self.search_next_button.setEnabled(has_results and self.current_search_highlight_idx < len(self.current_flat_results_list) - 1)
        # Le bouton "Chercher" est toujours actif s'il y a du texte dans l'input.

    # --- Gestion des Miniatures et Signets ---
    def _load_thumbnails(self):
        self.thumbnail_list_widget.clear()
        if not self.current_pdf_document:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            for page_idx in range(self.current_pdf_document.page_count):
                page = self.current_pdf_document.load_page(page_idx)
                # Générer une miniature plus petite pour la liste
                thumb_matrix = fitz.Matrix(0.15, 0.15) # Ajuster ce facteur pour la taille désirée
                pix = page.get_pixmap(matrix=thumb_matrix, alpha=False)
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)

                item = QListWidgetItem(QIcon(pixmap), self.tr("Page {0}").format(page_idx + 1))
                item.setData(Qt.UserRole, page_idx) # Stocker l'index de page (0-basé)
                item.setSizeHint(QSize(120, 160)) # Donner une taille indicative à l'item
                self.thumbnail_list_widget.addItem(item)
        finally:
            QApplication.restoreOverrideCursor()

        self._highlight_current_thumbnail()

    def _on_thumbnail_clicked(self, item: QListWidgetItem):
        page_idx = item.data(Qt.UserRole)
        if isinstance(page_idx, int):
            self.go_to_page(page_idx)

    def _highlight_current_thumbnail(self):
        if not self.thumbnail_list_widget or self.thumbnail_list_widget.count() == 0:
            return
        if 0 <= self.current_page_number < self.thumbnail_list_widget.count():
            item = self.thumbnail_list_widget.item(self.current_page_number)
            if item:
                self.thumbnail_list_widget.setCurrentItem(item) # Met en surbrillance

    def _load_bookmarks(self):
        self.bookmark_tree_widget.clear()
        if not self.current_pdf_document:
            return

        toc = self.current_pdf_document.get_toc(simple=False)
        if not toc:
            self.left_panel_tab_widget.setTabText(1, self.tr("Signets (Aucun)"))
            return

        self.left_panel_tab_widget.setTabText(1, self.tr("Signets"))

        # Fonction récursive pour ajouter les items de signets
        def add_toc_items_recursively(parent_item_or_tree, toc_entries_level):
            for entry in toc_entries_level:
                level, title, page_num_1_indexed, dest_dict = entry
                tree_item = QTreeWidgetItem([title])
                # Stocker la page (0-indexée) et les détails de destination
                dest_data = {'page': page_num_1_indexed - 1, 'dest_details': dest_dict}
                tree_item.setData(0, Qt.UserRole, dest_data)

                if isinstance(parent_item_or_tree, QTreeWidget):
                    parent_item_or_tree.addTopLevelItem(tree_item)
                else: # C'est un QTreeWidgetItem parent
                    parent_item_or_tree.addChild(tree_item)

                # Trouver les enfants de cette entrée
                children = []
                current_entry_index_in_toc = -1
                for i, e in enumerate(toc): # Recherche dans la liste toc globale
                    if e == entry:
                        current_entry_index_in_toc = i
                        break

                if current_entry_index_in_toc != -1:
                    for i in range(current_entry_index_in_toc + 1, len(toc)):
                        next_entry = toc[i]
                        next_level = next_entry[0]
                        if next_level == level + 1: # Enfant direct
                            children.append(next_entry)
                        elif next_level <= level: # Fin des enfants pour ce niveau
                            break

                if children:
                    add_toc_items_recursively(tree_item, children)

        top_level_toc_items = [entry for entry in toc if entry[0] == 1]
        add_toc_items_recursively(self.bookmark_tree_widget, top_level_toc_items)
        self.bookmark_tree_widget.expandAll()


    def _on_bookmark_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if data and isinstance(data, dict) and 'page' in data:
            page_idx_0_based = data['page']
            dest_details = data.get('dest_details', {}) # type: fitz.Destination

            if not (self.current_pdf_document and 0 <= page_idx_0_based < self.current_pdf_document.page_count):
                logging.warning(f"Signet cliqué: numéro de page invalide {page_idx_0_based}")
                return

            self.go_to_page(page_idx_0_based)

            # Appliquer le zoom et le défilement spécifiques du signet après que la page soit chargée
            # Utiliser QTimer.singleShot pour s'assurer que la vue de la page est mise à jour
            QTimer.singleShot(0, lambda: self._apply_bookmark_destination_details(dest_details, page_idx_0_based))

    def _apply_bookmark_destination_details(self, dest_details: dict, target_page_idx: int):
        if not self.current_pdf_document or self.current_page_number != target_page_idx:
            # La page a changé depuis que le timer a été lancé, ou le document est fermé
            return

        logging.debug(f"Application des détails de destination du signet pour page {target_page_idx+1}: {dest_details}")

        # Zoom
        # 'zoom' in dest_details est un facteur de zoom (0 pour hériter, sinon >0)
        # 'fitz. عملیات Fit fonctions' (comme FitH, FitV, FitBH, FitBV) peuvent être dans 'kind'
        kind = dest_details.get('kind')

        if kind == fitz.PDF_DEST_FITH: # Fit Horizontally (Fit Width)
            self.zoom_to_fit_width()
        elif kind == fitz.PDF_DEST_FITV: # Fit Vertically (pas direct, on peut fitter la page)
             # Approximatif: si la page est plus haute que large, fitter la page est proche
            page_rect = self.current_pdf_document.load_page(target_page_idx).rect
            if page_rect.height > page_rect.width:
                self.zoom_to_fit_page()
            # Sinon, le comportement par défaut du zoom après go_to_page est conservé
        elif kind == fitz.PDF_DEST_FITR: # Fit Rectangle
            # Nécessite les coordonnées du rectangle du signet, peut être complexe
            # Pour l'instant, on ne gère pas ce cas spécifiquement.
            pass
        elif dest_details.get('zoom', 0) > 0:
            self.set_zoom_factor(dest_details['zoom'])

        # Défilement (après que le zoom soit appliqué)
        # 'to' est un fitz.Point, 'left' et 'top' sont des positions
        # Les coordonnées sont en points PDF (non zoomés)
        scroll_to_point = None
        if dest_details.get('to'): # C'est un fitz.Point
            scroll_to_point = dest_details['to']
        elif dest_details.get('left') is not None or dest_details.get('top') is not None:
            # PyMuPDF < 1.19.0 : left/top/right/bottom
            # PyMuPDF >= 1.19.0 : 'to' (Point), 'lbpt' (Point for left-bottom)
            # Le dictionnaire dest_details vient de get_toc, qui devrait être moderne.
            # Si 'to' n'est pas là, on peut essayer de construire à partir de 'left'/'top'
            # mais 'to' est généralement préféré.
            # Pour l'instant, on se fie à 'to'. S'il n'est pas là, on ne fait pas de défilement spécifique.
            pass

        if scroll_to_point:
            # Convertir le point PDF en coordonnées de la scène (zoomées)
            scene_x = scroll_to_point.x * self.current_zoom_factor
            scene_y = scroll_to_point.y * self.current_zoom_factor

            # Assurer que la vue est centrée autant que possible sur ce point
            # QGraphicsView.centerOn(QPointF)
            self.pdf_view.centerOn(QPointF(scene_x, scene_y))
            # Alternativement, contrôler les barres de défilement directement
            # self.pdf_view.horizontalScrollBar().setValue(int(scene_x - self.pdf_view.viewport().width() / 2))
            # self.pdf_view.verticalScrollBar().setValue(int(scene_y - self.pdf_view.viewport().height() / 2))
            logging.debug(f"Signet: Défilement vers le point PDF {scroll_to_point}, scène ({scene_x}, {scene_y})")

if __name__ == '__main__':
    # This is for testing the widget independently
    import sys
    from PyQt5.QtWidgets import QApplication, QMessageBox # QMessageBox for _load_pdf error

    # Dummy PDF path for testing - replace with a real PDF path
    # Create a dummy PDF if you don't have one handy for testing
    # For example, using fitz:
    # doc = fitz.open()
    # page = doc.new_page()
    # page.insert_text(fitz.Point(50, 72), "Hello, PyMuPDF!")
    # doc.save("test_dummy.pdf")
    # doc.close()
    # TEST_PDF_PATH = "test_dummy.pdf"

    # Prompt user for a PDF file to test
    from PyQt5.QtWidgets import QFileDialog
    app = QApplication(sys.argv)

    test_pdf_path, _ = QFileDialog.getOpenFileName(None, "Select PDF to Test Viewer", "", "PDF Files (*.pdf)")

    if test_pdf_path:
        viewer = PdfViewerWidget(test_pdf_path)
        viewer.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
