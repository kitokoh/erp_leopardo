import sys
import fitz  # PyMuPDF
import logging # Logging module

from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QMenu, QMenuBar,
                             QToolBar, QDockWidget, QLabel, QVBoxLayout, QWidget,
                             QListWidget, QTextEdit, QFileDialog, QMessageBox,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QPushButton, QHBoxLayout, QSpinBox, QScrollArea)
from PyQt5.QtCore import Qt, QSize, QRectF
from PyQt5.QtGui import QIcon, QPixmap, QImage

# Configuration du logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)]) # Sortie console pour le moment

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Initialisation de MainWindow.")
        self.setWindowTitle("Éditeur PDF PyQt")
        self.setGeometry(100, 100, 1200, 800)

        self.current_pdf_document = None
        self.current_page_number = 0
        self.current_zoom_factor = 1.0
        self.is_document_modified = False # Ajouté ici explicitement
        self.current_tool_mode = None
        self.highlight_color = (1, 1, 0)
        self.ink_color = (0, 0, 1)
        self.ink_thickness = 1.5
        self.shape_border_color = (1, 0, 0) # Rouge par défaut pour contour formes
        self.shape_fill_color = None # Pas de remplissage par défaut (None)
        self.shape_border_width = 1.5
        self.selection_start_point = None
        self.selection_rect_item = None
        self.current_ink_stroke = []
        self.temp_ink_item = None
        self.selected_annotation = None # Pour stocker l'annotation fitz sélectionnée
        self.selected_annotation_bbox_item = None # Pour visualiser la sélection d'une annotation

        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bars()
        self._setup_central_widget()
        self._create_dock_widgets()
        self._create_navigation_bar()


        self.statusBar().showMessage("Prêt")

    def _create_actions(self):
        # Actions Fichier
        self.open_action = QAction(QIcon.fromTheme("document-open", QIcon(":/icons/document-open.png")), "&Ouvrir...", self)
        self.open_action.setStatusTip("Ouvrir un fichier PDF")
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction(QIcon.fromTheme("document-save", QIcon(":/icons/document-save.png")), "&Enregistrer", self)
        self.save_action.setStatusTip("Enregistrer le fichier PDF actuel")
        self.save_action.triggered.connect(self.save_file)
        self.save_action.setEnabled(False)

        self.save_as_action = QAction(QIcon.fromTheme("document-save-as", QIcon(":/icons/document-save-as.png")), "Enregistrer &sous...", self)
        self.save_as_action.setStatusTip("Enregistrer le fichier PDF actuel sous un nouveau nom")
        self.save_as_action.triggered.connect(self.save_file_as)
        self.save_as_action.setEnabled(False)

        self.exit_action.setStatusTip("Quitter l'application")
        self.exit_action.triggered.connect(self.close)

        # Actions Zoom
        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon(":/icons/zoom-in.png")), "Zoom &Avant", self)
        self.zoom_in_action.setStatusTip("Zoomer en avant")
        self.zoom_in_action.triggered.connect(lambda: self.zoom(1.2))
        self.zoom_in_action.setEnabled(False)

        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon(":/icons/zoom-out.png")), "Zoom &Arrière", self)
        self.zoom_out_action.setStatusTip("Zoomer en arrière")
        self.zoom_out_action.triggered.connect(lambda: self.zoom(0.8))
        self.zoom_out_action.setEnabled(False)

        self.zoom_original_action = QAction(QIcon.fromTheme("zoom-original", QIcon(":/icons/zoom-original.png")), "Zoom &Original", self)
        self.zoom_original_action.setStatusTip("Afficher à la taille originale (100%)")
        self.zoom_original_action.triggered.connect(lambda: self.set_zoom_factor(1.0))
        self.zoom_original_action.setEnabled(False)

        # Actions de Navigation
        self.prev_page_action = QAction(QIcon.fromTheme("go-previous", QIcon(":/icons/go-previous.png")), "Page &Précédente", self)
        self.prev_page_action.setStatusTip("Aller à la page précédente")
        self.prev_page_action.triggered.connect(self.go_to_previous_page)
        self.prev_page_action.setEnabled(False)

        self.next_page_action.setStatusTip("Aller à la page suivante")
        self.next_page_action.triggered.connect(self.go_to_next_page)
        self.next_page_action.setEnabled(False)

        # Action de Suppression de Page
        self.delete_page_action.setStatusTip("Supprimer la page actuellement sélectionnée ou affichée")
        self.delete_page_action.triggered.connect(self.delete_current_page)
        self.delete_page_action.setEnabled(False)

        # Action d'Insertion de Page Vierge
        self.insert_blank_page_action.setStatusTip("Insérer une nouvelle page vierge dans le document")
        self.insert_blank_page_action.triggered.connect(self.insert_blank_page)
        self.insert_blank_page_action.setEnabled(False)

        # Action d'Importation de Pages PDF
        self.import_pages_action.setStatusTip("Importer des pages d'un autre fichier PDF")
        self.import_pages_action.triggered.connect(self.import_pages_from_pdf)
        self.import_pages_action.setEnabled(False)

        # Actions de Rotation de Page
        self.rotate_cw_action = QAction(QIcon.fromTheme("object-rotate-right", QIcon(":/icons/object-rotate-right.png")), "Rotation Horaire (90°)", self)
        self.rotate_cw_action.setStatusTip("Pivoter la page actuelle de 90° dans le sens horaire")
        self.rotate_cw_action.triggered.connect(lambda: self.rotate_current_page(90))
        self.rotate_cw_action.setEnabled(False)

        self.rotate_ccw_action = QAction(QIcon.fromTheme("object-rotate-left", QIcon(":/icons/object-rotate-left.png")), "Rotation Anti-horaire (90°)", self)
        self.rotate_ccw_action.setStatusTip("Pivoter la page actuelle de 90° dans le sens anti-horaire")
        self.rotate_ccw_action.triggered.connect(lambda: self.rotate_current_page(-90))
        self.rotate_ccw_action.setEnabled(False)

        # Action de Rognage de Page
        self.crop_page_action = QAction(QIcon.fromTheme("transform-crop", QIcon(":/icons/transform-crop.png")), "&Rogner la Page...", self)
        self.crop_page_action.setStatusTip("Rogner la page actuelle pour en réduire les dimensions visibles")
        self.crop_page_action.triggered.connect(self.crop_current_page)
        self.crop_page_action.setEnabled(False)

        # Actions d'Annotation
        self.highlight_action = QAction(QIcon.fromTheme("format-text-highlight", QIcon(":/icons/format-text-highlight.png")), "&Surligner Texte", self)
        self.highlight_action.setStatusTip("Activer l'outil de surlignage de texte")
        self.highlight_action.setCheckable(True)
        self.highlight_action.triggered.connect(self.toggle_highlight_mode)
        self.highlight_action.setEnabled(False)

        self.ink_action = QAction(QIcon.fromTheme("draw-freehand", QIcon(":/icons/draw-freehand.png")), "&Dessin (Stylo)", self)
        self.ink_action.setStatusTip("Activer l'outil de dessin à main levée")
        self.ink_action.setCheckable(True)
        self.ink_action.triggered.connect(self.toggle_ink_mode)
        self.ink_action.setEnabled(False)

        self.rect_annot_action = QAction(QIcon.fromTheme("draw-rectangle", QIcon(":/icons/draw-rectangle.png")), "Dessiner &Rectangle", self)
        self.rect_annot_action.setStatusTip("Activer l'outil de dessin de rectangle")
        self.rect_annot_action.setCheckable(True)
        self.rect_annot_action.triggered.connect(self.toggle_rect_annot_mode)
        self.rect_annot_action.setEnabled(False)

        self.circle_annot_action = QAction(QIcon.fromTheme("draw-ellipse", QIcon(":/icons/draw-ellipse.png")), "Dessiner &Cercle/Ellipse", self)
        self.circle_annot_action.setStatusTip("Activer l'outil de dessin de cercle/ellipse")
        self.circle_annot_action.setCheckable(True)
        self.circle_annot_action.triggered.connect(self.toggle_circle_annot_mode)
        self.circle_annot_action.setEnabled(False)

        self.line_annot_action = QAction(QIcon.fromTheme("draw-line", QIcon(":/icons/draw-line.png")), "Dessiner &Ligne", self)
        self.line_annot_action.setStatusTip("Activer l'outil de dessin de ligne")
        self.line_annot_action.setCheckable(True)
        self.line_annot_action.triggered.connect(self.toggle_line_annot_mode)
        self.line_annot_action.setEnabled(False)

        self.text_annot_action = QAction(QIcon.fromTheme("mail-mark-unread", QIcon(":/icons/note-add.png")), "Ajouter une &Note Textuelle", self) # Icone à trouver/créer
        self.text_annot_action.setStatusTip("Activer l'outil d'ajout de note textuelle (commentaire)")
        self.text_annot_action.setCheckable(True)
        self.text_annot_action.triggered.connect(self.toggle_text_annot_mode)
        self.text_annot_action.setEnabled(False)

        # Action de suppression d'annotation
        self.delete_selected_annot_action = QAction(QIcon.fromTheme("edit-clear", QIcon(":/icons/edit-clear.png")), "Supprimer l'Annotation", self)
        self.delete_selected_annot_action.setStatusTip("Supprimer l'annotation actuellement sélectionnée")
        self.delete_selected_annot_action.triggered.connect(self.delete_selected_annotation)
        self.delete_selected_annot_action.setEnabled(False) # Activée si une annotation est sélectionnée


    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # Menu Fichier
        file_menu = menu_bar.addMenu("&Fichier")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # Menu Édition
        edit_menu = menu_bar.addMenu("&Édition")
        edit_menu.addAction(self.delete_page_action)
        edit_menu.addAction(self.insert_blank_page_action)
        edit_menu.addAction(self.import_pages_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.rotate_cw_action)
        edit_menu.addAction(self.rotate_ccw_action)
        edit_menu.addAction(self.crop_page_action)

        # Menu Outils d'Annotation (pourrait être un sous-menu d'Édition ou Outils)
        annotation_menu = menu_bar.addMenu("&Annotation")
        annotation_menu.addAction(self.highlight_action)
        annotation_menu.addAction(self.ink_action)
        annotation_menu.addSeparator()
        annotation_menu.addAction(self.rect_annot_action)
        annotation_menu.addAction(self.circle_annot_action)
        annotation_menu.addAction(self.line_annot_action)
        annotation_menu.addSeparator()
        annotation_menu.addAction(self.text_annot_action)
        annotation_menu.addSeparator()
        annotation_menu.addAction(self.delete_selected_annot_action)
        # Plus tard: Annuler, Rétablir, Couper, Copier, Coller, etc.

        # Menu Vue
        view_menu = menu_bar.addMenu("&Vue")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.zoom_original_action)
        view_menu.addSeparator()
        # Plus tard: actions pour montrer/cacher les panneaux latéraux
        view_menu.addAction(self.page_thumbnails_dock.toggleViewAction())
        view_menu.addAction(self.bookmarks_dock.toggleViewAction())
        view_menu.addAction(self.properties_dock.toggleViewAction())


        # Menu Outils (sera rempli plus tard)
        tools_menu = menu_bar.addMenu("&Outils")
        tools_menu.addAction(self.prev_page_action) # Temporairement ici pour test
        tools_menu.addAction(self.next_page_action) # Temporairement ici pour test


        # Menu Aide (sera rempli plus tard)
        help_menu = menu_bar.addMenu("&Aide")
        # help_menu.addAction(...)

    def _create_tool_bars(self):
        # Barre d'outils Fichier
        file_tool_bar = self.addToolBar("Fichier")
        file_tool_bar.setIconSize(QSize(24, 24))
        file_tool_bar.addAction(self.open_action)
        file_tool_bar.addAction(self.save_action)
        file_tool_bar.addAction(self.save_as_action)

        # Barre d'outils Navigation et Zoom
        navi_zoom_tool_bar = self.addToolBar("Navigation & Zoom")
        navi_zoom_tool_bar.setIconSize(QSize(24,24))
        navi_zoom_tool_bar.addAction(self.prev_page_action)
        navi_zoom_tool_bar.addAction(self.next_page_action)
        navi_zoom_tool_bar.addSeparator()
        navi_zoom_tool_bar.addAction(self.zoom_out_action)
        navi_zoom_tool_bar.addAction(self.zoom_in_action)
        navi_zoom_tool_bar.addAction(self.zoom_original_action)

        # Barre d'outils Manipulation de Page (pourrait être fusionnée ou séparée)
        page_manip_tool_bar = self.addToolBar("Manipulation de Page")
        page_manip_tool_bar.setIconSize(QSize(24,24))
        page_manip_tool_bar.addAction(self.rotate_ccw_action)
        page_manip_tool_bar.addAction(self.rotate_cw_action)
        page_manip_tool_bar.addAction(self.delete_page_action)
        page_manip_tool_bar.addAction(self.crop_page_action)
        # On pourrait y ajouter aussi insert_blank_page_action et import_pages_action

        # Barre d'outils Annotation
        annotation_tool_bar = self.addToolBar("Annotation")
        annotation_tool_bar.setIconSize(QSize(24,24))
        annotation_tool_bar.addAction(self.highlight_action)
        annotation_tool_bar.addAction(self.ink_action)
        annotation_tool_bar.addSeparator()
        annotation_tool_bar.addAction(self.rect_annot_action)
        annotation_tool_bar.addAction(self.circle_annot_action)
        annotation_tool_bar.addAction(self.line_annot_action)
        annotation_tool_bar.addSeparator()
        annotation_tool_bar.addAction(self.text_annot_action)


    def _setup_central_widget(self):
        self.pdf_view = QGraphicsView(self)
        self.pdf_scene = QGraphicsScene(self)
        self.pdf_view.setScene(self.pdf_scene)
        self.pdf_view_item = QGraphicsPixmapItem() # Pour afficher la page PDF rendue
        self.pdf_scene.addItem(self.pdf_view_item)

        # Connecter les événements de la souris pour la sélection
        self.pdf_view.mousePressEvent = self.graphics_view_mouse_press
        self.pdf_view.mouseMoveEvent = self.graphics_view_mouse_move
        self.pdf_view.mouseReleaseEvent = self.graphics_view_mouse_release

        # Pour permettre le défilement si l'image est plus grande que la vue
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.pdf_view)
        self.setCentralWidget(scroll_area)


    def _create_dock_widgets(self):
        # Panneau des miniatures de pages
        self.page_thumbnails_dock = QDockWidget("Miniatures des Pages", self)
        self.page_thumbnails_list = QListWidget()
        self.page_thumbnails_list.itemClicked.connect(self.go_to_page_from_thumbnail)

        # Configuration pour le Drag & Drop
        self.page_thumbnails_list.setDragEnabled(True)
        self.page_thumbnails_list.setAcceptDrops(True)
        self.page_thumbnails_list.setDropIndicatorShown(True)
        self.page_thumbnails_list.setDefaultDropAction(Qt.MoveAction)
        self.page_thumbnails_list.model().rowsMoved.connect(self.on_thumbnail_rows_moved)

        self.page_thumbnails_dock.setWidget(self.page_thumbnails_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.page_thumbnails_dock)

        # Panneau des signets/table des matières
        self.bookmarks_dock = QDockWidget("Signets / Table des Matières", self)
        self.bookmarks_tree = QListWidget() # Sera un QTreeWidget plus tard
        # self.bookmarks_tree.itemClicked.connect(self.go_to_bookmark) # Sera implémenté
        self.bookmarks_dock.setWidget(self.bookmarks_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bookmarks_dock)
        self.tabifyDockWidget(self.page_thumbnails_dock, self.bookmarks_dock)

        # Panneau des propriétés
        self.properties_dock = QDockWidget("Propriétés", self)
        self.properties_editor = QTextEdit() # Placeholder
        self.properties_editor.setReadOnly(True)
        self.properties_dock.setWidget(self.properties_editor)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)

    def _create_navigation_bar(self):
        # Barre de navigation en bas (peut être une barre d'outils ou un widget custom)
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)

        self.prev_page_button = QPushButton(QIcon.fromTheme("go-previous"), "<")
        self.prev_page_button.clicked.connect(self.go_to_previous_page)
        self.prev_page_button.setEnabled(False)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setEnabled(False)
        self.page_spinbox.valueChanged.connect(self.go_to_page_from_spinbox)

        self.total_pages_label = QLabel("/ N/A")

        self.next_page_button = QPushButton(QIcon.fromTheme("go-next"), ">")
        self.next_page_button.clicked.connect(self.go_to_next_page)
        self.next_page_button.setEnabled(False)

        nav_layout.addStretch()
        nav_layout.addWidget(self.prev_page_button)
        nav_layout.addWidget(self.page_spinbox)
        nav_layout.addWidget(self.total_pages_label)
        nav_layout.addWidget(self.next_page_button)
        nav_layout.addStretch()

        # Ajout comme une barre d'outils en bas
        navigation_toolbar = QToolBar("Navigation")
        navigation_toolbar.setMovable(False)
        navigation_toolbar.addWidget(nav_widget)
        self.addToolBar(Qt.BottomToolBarArea, navigation_toolbar)


    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier PDF", "", "Fichiers PDF (*.pdf);;Tous les fichiers (*)")
        if file_path:
            try:
                self.current_pdf_document = fitz.open(file_path)
                self.current_page_number = 0
                self.current_zoom_factor = 1.0
                self.update_page_view()
                self.update_thumbnails()
                self.update_navigation_controls()
                self.save_action.setEnabled(True)
                self.save_as_action.setEnabled(True)
                self.zoom_in_action.setEnabled(True)
                self.zoom_out_action.setEnabled(True)
                self.zoom_original_action.setEnabled(True)
                self.statusBar().showMessage(f"Ouvert : {file_path}")
                logging.info(f"Fichier PDF ouvert : {file_path}")
            except Exception as e:
                logging.error(f"Erreur lors de l'ouverture du PDF {file_path}: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur d'ouverture", f"Impossible d'ouvrir le fichier PDF '{file_path}'.\nErreur : {e}")
                self.current_pdf_document = None
                # Réinitialiser l'état de l'interface
                self._reset_ui_on_error()


    def _reset_ui_on_error(self):
        """Réinitialise certains éléments de l'interface en cas d'erreur de chargement de PDF."""
        self.pdf_scene.clear()
        self.pdf_view_item = QGraphicsPixmapItem()
        self.pdf_scene.addItem(self.pdf_view_item)
        self.pdf_view_item.setPixmap(QPixmap())
        self.setWindowTitle("Éditeur PDF PyQt")
        self.page_thumbnails_list.clear()
        self.update_navigation_controls() # Cela désactivera les boutons etc.
        self.save_action.setEnabled(False)
        self.save_as_action.setEnabled(False)
        self.zoom_in_action.setEnabled(False)
        self.zoom_out_action.setEnabled(False)
        self.zoom_original_action.setEnabled(False)
        self.delete_page_action.setEnabled(False)
        self.insert_blank_page_action.setEnabled(False)
        self.import_pages_action.setEnabled(False)
        self.rotate_cw_action.setEnabled(False)
        self.rotate_ccw_action.setEnabled(False)
        self.crop_page_action.setEnabled(False)
        self.highlight_action.setEnabled(False)
        self.highlight_action.setChecked(False)
        self.ink_action.setEnabled(False)
        self.ink_action.setChecked(False)
        self.rect_annot_action.setEnabled(False)
        self.rect_annot_action.setChecked(False)
        self.circle_annot_action.setEnabled(False)
        self.circle_annot_action.setChecked(False)
        self.line_annot_action.setEnabled(False)
        self.line_annot_action.setChecked(False)
        self.text_annot_action.setEnabled(False) # Désactiver ajout de note
        self.text_annot_action.setChecked(False)
        self.current_tool_mode = None
        self.statusBar().showMessage("Erreur lors du chargement du PDF. Prêt.")


    def update_page_view(self):
        if not self.current_pdf_document or self.current_page_number < 0 or self.current_page_number >= self.current_pdf_document.page_count:
            logging.debug("update_page_view appelé sans document valide ou numéro de page hors limites.")
            self._reset_ui_on_error() # Utiliser la méthode de réinitialisation
            return

        try:
            page = self.current_pdf_document.load_page(self.current_page_number)
            logging.debug(f"Affichage de la page {self.current_page_number + 1} avec zoom {self.current_zoom_factor:.2f}")
        except Exception as e:
            logging.error(f"Impossible de charger la page {self.current_page_number}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de Page", f"Impossible de charger la page {self.current_page_number + 1}.\nErreur: {e}")
            self._reset_ui_on_error()
            return

        # Utiliser une matrice de transformation pour le zoom
        matrix = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor)
        pix = page.get_pixmap(matrix=matrix)

        image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
        pixmap = QPixmap.fromImage(qimage)

        self.pdf_scene.clear() # Important pour enlever l'ancienne page/item
        self.pdf_view_item = QGraphicsPixmapItem(pixmap)
        self.pdf_scene.addItem(self.pdf_view_item)
        self.pdf_scene.setSceneRect(QRectF(pixmap.rect())) # Ajuster la taille de la scène

        self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1}/{self.current_pdf_document.page_count}")
        self.update_navigation_controls()

    def update_thumbnails(self):
        self.page_thumbnails_list.clear()
        if self.current_pdf_document:
            for i in range(self.current_pdf_document.page_count):
                page = self.current_pdf_document.load_page(i)
                # Créer des miniatures plus petites
                thumb_matrix = fitz.Matrix(0.2, 0.2) # Facteur de zoom pour miniature
                pix = page.get_pixmap(matrix=thumb_matrix)
                image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
                pixmap = QPixmap.fromImage(qimage)

                item = QListWidgetItem(QIcon(pixmap), f"Page {i + 1}")
                self.page_thumbnails_list.addItem(item)
            self.page_thumbnails_list.setCurrentRow(self.current_page_number)


    def update_navigation_controls(self):
        if self.current_pdf_document:
            num_pages = self.current_pdf_document.page_count
            self.prev_page_action.setEnabled(self.current_page_number > 0)
            self.next_page_action.setEnabled(self.current_page_number < num_pages - 1)
            self.prev_page_button.setEnabled(self.current_page_number > 0)
            self.next_page_button.setEnabled(self.current_page_number < num_pages - 1)

            self.page_spinbox.setEnabled(True)
            self.page_spinbox.blockSignals(True) # Bloquer signaux pour éviter appel récursif
            self.page_spinbox.setRange(1, num_pages)
            self.page_spinbox.setValue(self.current_page_number + 1)
            self.page_spinbox.blockSignals(False) # Réactiver signaux
            self.total_pages_label.setText(f"/ {num_pages}")
        else:
            self.prev_page_action.setEnabled(False)
            self.next_page_action.setEnabled(False)
            self.prev_page_button.setEnabled(False)
            self.next_page_button.setEnabled(False)
            self.page_spinbox.setEnabled(False)
            self.total_pages_label.setText("/ N/A")

    def go_to_page(self, page_num):
        if self.current_pdf_document and 0 <= page_num < self.current_pdf_document.page_count:
            self.current_page_number = page_num
            self.update_page_view()
            self.page_thumbnails_list.setCurrentRow(self.current_page_number)

    def go_to_previous_page(self):
        self.go_to_page(self.current_page_number - 1)

    def go_to_next_page(self):
        self.go_to_page(self.current_page_number + 1)

    def go_to_page_from_thumbnail(self, item):
        row = self.page_thumbnails_list.row(item)
        self.go_to_page(row)

    def go_to_page_from_spinbox(self, value):
        self.go_to_page(value - 1) # Spinbox est 1-based

    def zoom(self, factor):
        self.current_zoom_factor *= factor
        self.update_page_view()
        self.zoom_original_action.setEnabled(self.current_zoom_factor != 1.0)


    def set_zoom_factor(self, factor):
        self.current_zoom_factor = factor
        self.update_page_view()
        self.zoom_original_action.setEnabled(self.current_zoom_factor != 1.0)

    def save_file(self):
        # Actuellement, 'is_modified' n'est pas un attribut direct de fitz.Document.
        # Nous devrons implémenter notre propre suivi des modifications (is_document_modified).
        # Pour cette phase, la sauvegarde est destructive (écrase l'original avec save())
        # ou crée un nouveau fichier (avec save_as()).

        if not self.current_pdf_document:
            logging.warning("Tentative de sauvegarde sans document chargé.")
            # QMessageBox.warning(self, "Aucun document", "Aucun document n'est ouvert pour la sauvegarde.") # Optionnel
            return

        # Si le document a un chemin (attribut 'name' de fitz.Document après ouverture/sauvegarde)
        # et que nous n'avons pas encore de logique de "modifications en attente",
        # on peut soit ne rien faire, soit forcer une sauvegarde (ce qui est fait ici).
        # Idéalement, on vérifierait un flag self.is_document_modified.

        file_path_to_save = ""
        if hasattr(self.current_pdf_document, 'name') and self.current_pdf_document.name:
             file_path_to_save = self.current_pdf_document.name

        if not file_path_to_save: # Si le document n'a pas de nom (ex: nouveau doc non encore implémenté, ou erreur)
            self.save_file_as()
            return

        try:
            # Options de sauvegarde : garbage=3 (nettoyage), deflate=True (compression)
            self.current_pdf_document.save(file_path_to_save, garbage=3, deflate=True)
            self.statusBar().showMessage(f"Fichier sauvegardé : {file_path_to_save}")
            logging.info(f"Fichier PDF sauvegardé : {file_path_to_save}")
            # self.is_document_modified = False # Réinitialiser le flag de modification
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du PDF {file_path_to_save}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de sauvegarde", f"Impossible de sauvegarder le fichier '{file_path_to_save}'.\nErreur : {e}")

    def save_file_as(self):
        if not self.current_pdf_document:
            logging.warning("Tentative de 'Enregistrer sous' sans document chargé.")
            QMessageBox.warning(self, "Aucun document", "Aucun document n'est ouvert pour l'enregistrement.")
            return

        current_dir = ""
        if hasattr(self.current_pdf_document, 'name') and self.current_pdf_document.name:
             current_dir = self.current_pdf_document.name # Utiliser le chemin du fichier actuel comme point de départ

        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le PDF sous...", current_dir, "Fichiers PDF (*.pdf)")

        if file_path:
            try:
                self.current_pdf_document.save(file_path, garbage=3, deflate=True)
                self.statusBar().showMessage(f"Fichier sauvegardé sous : {file_path}")
                logging.info(f"Fichier PDF sauvegardé sous : {file_path}")

                # Mettre à jour le document actuel pour qu'il pointe vers le nouveau fichier
                original_page_number = self.current_page_number # Sauver la page actuelle
                self.current_pdf_document.close()
                self.current_pdf_document = fitz.open(file_path)
                self.current_page_number = original_page_number # Restaurer la page
                if self.current_page_number >= self.current_pdf_document.page_count: # Au cas où le nouveau doc est plus court
                    self.current_page_number = max(0, self.current_pdf_document.page_count -1)

                # Mettre à jour l'interface (titre, miniatures, etc.)
                self.update_page_view() # Pour le titre et la page
                self.update_thumbnails() # Mettre à jour les miniatures
                self.update_navigation_controls() # Pour le nombre total de pages etc.
                self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1}/{self.current_pdf_document.page_count} [{file_path}]")
                # self.is_document_modified = False # Réinitialiser le flag de modification

            except Exception as e:
                logging.error(f"Erreur lors de 'Enregistrer sous' pour le PDF {file_path}: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur de sauvegarde", f"Impossible d'enregistrer le fichier sous '{file_path}'.\nErreur : {e}")

    def _ask_save_before_action(self):
        """
        Demande à l'utilisateur s'il veut sauvegarder avant une action qui pourrait perdre des données
        (comme ouvrir un nouveau fichier, ou quitter).
        Retourne True si l'action peut continuer, False si elle doit être annulée.
        """
        # TODO: Implémenter un vrai self.is_document_modified
        # Pour l'instant, on part du principe que si un document est ouvert, il *pourrait* être modifié.
        if not self.current_pdf_document: # Pas de document, pas de souci
            return True

        # Simuler pour l'instant que le document est toujours "potentiellement" modifié s'il est ouvert
        # Dans une version future, on aura un flag self.is_document_modified
        user_choice = QMessageBox.question(self,
                                           "Modifications non sauvegardées",
                                           "Le document actuel a peut-être des modifications non sauvegardées. "
                                           "Voulez-vous les sauvegarder avant de continuer ?",
                                           QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                           QMessageBox.Cancel) # Default to Cancel

        if user_choice == QMessageBox.Save:
            self.save_file()
            # Ici, il faudrait vérifier si la sauvegarde a réussi (pas annulée par l'utilisateur dans la boîte de dialogue save_as)
            # Pour l'instant, on assume que la sauvegarde réussit si l'utilisateur choisit "Save".
            # Si self.save_file() appelle save_file_as() et que l'utilisateur annule, on est bloqué.
            # Une meilleure gestion serait que save_file retourne un booléen.
            # Pour la simplicité de cette phase, on continue.
            return True
        elif user_choice == QMessageBox.Discard:
            return True # L'utilisateur choisit de perdre les modifications
        elif user_choice == QMessageBox.Cancel:
            return False # L'utilisateur annule l'action (ex: ouvrir nouveau fichier / quitter)
        return False # Par défaut, annuler si quelque chose d'inattendu se passe


    def closeEvent(self, event):
        logging.info("Tentative de fermeture de l'application via closeEvent.")
        if self._ask_save_before_action():
            logging.info("Fermeture de l'application autorisée.")
            if self.current_pdf_document:
                try:
                    self.current_pdf_document.close()
                    logging.debug("Document PDF fermé dans closeEvent.")
                except Exception as e:
                    logging.warning(f"Erreur à la fermeture du document PDF dans closeEvent: {e}")
                self.current_pdf_document = None
            super().closeEvent(event)
        else:
            logging.info("Fermeture de l'application annulée par l'utilisateur.")
            event.ignore()

    def on_thumbnail_rows_moved(self, parent, start_row, end_row, destination_parent, destination_row):
        """Appelé lorsque des éléments sont déplacés dans la liste des miniatures."""
        if not self.current_pdf_document:
            return

        logging.debug(f"Déplacement de miniatures détecté : de {start_row} à {destination_row-1} (avant réorganisation interne de QListWidget)")

        # `destination_row` est l'index *avant lequel* les éléments sont insérés.
        # Si on déplace un élément vers le bas, destination_row peut être > nombre d'éléments.
        # Le QListWidget a déjà réorganisé ses éléments en interne au moment où ce signal est émis.
        # Nous devons déterminer la séquence originale des pages déplacées et leur nouvelle position.

        # Le nombre d'éléments déplacés
        count = end_row - start_row + 1

        # Obtenir les numéros de page originaux (0-indexed) des éléments qui ont été déplacés.
        # Ceci est délicat car le QListWidget a déjà bougé les items.
        # Une approche plus simple est de reconstruire l'ordre à partir du QListWidget.
        # Ou, si on déplace un seul item :

        if count == 1: # Cas simple: un seul item déplacé
            moved_page_original_index = start_row
            new_visual_index = destination_row

            # Ajuster new_visual_index si l'élément est déplacé vers le bas dans la liste
            # et que destination_row est après la position originale
            if new_visual_index > moved_page_original_index:
                new_visual_index -= 1 # L'index réel où il atterrit

            if moved_page_original_index == new_visual_index:
                logging.debug("L'élément a été déposé à sa position d'origine.")
                return

            logging.info(f"Déplacement de la page (index original {moved_page_original_index}) vers la nouvelle position visuelle {new_visual_index}")

            try:
                # PyMuPDF: move_page(page_num_to_move, new_page_num_target)
                # Les numéros sont 0-indexed. `new_page_num_target` est la position où la page atterrira.
                self.current_pdf_document.move_page(moved_page_original_index, new_visual_index)
                self.is_document_modified = True
                logging.info(f"Page PDF {moved_page_original_index} déplacée vers {new_visual_index} dans le document fitz.")

                # Mettre à jour l'affichage des miniatures pour refléter le nouvel ordre du document
                # et s'assurer que les textes des items ("Page X") sont corrects.
                # La page actuellement visualisée pourrait aussi avoir changé d'index.
                current_page_content_id = self.current_pdf_document[self.current_page_number].xref # Un moyen d'identifier la page

                self.update_thumbnails() # Cela va recréer les items dans le bon ordre

                # Retrouver le nouvel index de la page qui était affichée
                new_current_page_index = -1
                for i in range(self.current_pdf_document.page_count):
                    if self.current_pdf_document[i].xref == current_page_content_id:
                        new_current_page_index = i
                        break

                if new_current_page_index != -1 and self.current_page_number != new_current_page_index:
                    logging.debug(f"La page affichée ({self.current_page_number}) est maintenant à l'index {new_current_page_index}.")
                    self.current_page_number = new_current_page_index
                    # Pas besoin d'appeler update_page_view() si le contenu affiché est le même,
                    # mais les contrôles de navigation et le titre doivent être mis à jour.
                    self.update_navigation_controls()
                    self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1}/{self.current_pdf_document.page_count} [{self.current_pdf_document.name or ''}]")

                elif new_current_page_index == -1: # Ne devrait pas arriver
                     logging.error("Impossible de retrouver la page affichée après réorganisation.")
                     self.go_to_page(0) # Revenir à la première page par sécurité


                self.page_thumbnails_list.setCurrentRow(self.current_page_number) # S'assurer que la sélection est correcte
                self.statusBar().showMessage("Ordre des pages modifié.")

            except Exception as e:
                logging.error(f"Erreur lors du déplacement de la page PDF: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur de réorganisation", f"Impossible de réorganiser les pages.\nErreur: {e}")
                # Recharger les miniatures pour refléter l'état avant l'erreur (si possible)
                self.update_thumbnails()
        else:
            # La gestion du déplacement de plusieurs items en une seule fois est plus complexe
            # car le signal rowsMoved peut ne pas donner assez d'infos directes pour PyMuPDF.
            # Une stratégie serait de reconstruire l'ordre complet à partir du QListWidget
            # et d'appliquer une série de `move_page`.
            # Pour l'instant, on log un avertissement.
            logging.warning("Le déplacement de plusieurs miniatures à la fois n'est pas encore entièrement géré pour la réorganisation PDF.")
            # On met quand même à jour les miniatures pour que le QListWidget soit cohérent avec lui-même.
            # Cela ne réorganisera pas le PDF fitz pour l'instant dans ce cas.
            # Il faudrait une logique plus avancée ici.
            # Pour une solution temporaire et simple, on peut recharger les miniatures depuis le PDF
            # pour annuler visuellement le déplacement multiple si on ne le gère pas dans le PDF.
            self.update_thumbnails() # Annule le drag&drop visuel si non géré dans le PDF.
            QMessageBox.information(self, "Fonctionnalité Limitée", "Le déplacement de plusieurs pages à la fois n'est pas encore supporté pour la réorganisation du document PDF. Veuillez déplacer les pages une par une.")

    def delete_current_page(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0:
            logging.warning("Tentative de suppression de page sans document ou avec un document vide.")
            QMessageBox.warning(self, "Aucune page", "Aucune page à supprimer.")
            return

        # La page à supprimer est self.current_page_number
        page_to_delete_index = self.current_page_number
        page_count_before_delete = self.current_pdf_document.page_count

        if page_count_before_delete == 1:
            reply = QMessageBox.question(self, "Suppression de la dernière page",
                                           "Ceci est la dernière page du document. La suppression rendra le document vide. Continuer ?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        else:
            reply = QMessageBox.question(self, "Confirmation de suppression",
                                       f"Êtes-vous sûr de vouloir supprimer la page {page_to_delete_index + 1} ?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        try:
            logging.info(f"Tentative de suppression de la page {page_to_delete_index} (0-indexed).")
            self.current_pdf_document.delete_page(page_to_delete_index)
            self.is_document_modified = True
            logging.info(f"Page {page_to_delete_index} supprimée du document fitz.")

            self.statusBar().showMessage(f"Page {page_to_delete_index + 1} supprimée.")

            # Ajuster current_page_number si nécessaire
            if self.current_pdf_document.page_count == 0:
                self.current_page_number = -1 # Indique un document vide
                self._reset_ui_on_error() # Peut être utilisé pour nettoyer l'affichage
                self.delete_page_action.setEnabled(False)
                # On pourrait aussi fermer le document ou laisser un état "vide"
                # Pour l'instant, on le laisse ouvert mais vide.
                self.page_thumbnails_list.clear()
                self.total_pages_label.setText("/ 0")
                self.page_spinbox.setRange(0,0) # ou désactiver
                self.page_spinbox.setEnabled(False)
                self.prev_page_action.setEnabled(False)
                self.next_page_action.setEnabled(False)
                self.prev_page_button.setEnabled(False)
                self.next_page_button.setEnabled(False)

            else:
                # Si on a supprimé une page avant la fin, et que current_page_number
                # pointait sur la dernière page qui existe maintenant, c'est bon.
                # Si on a supprimé la page current_page_number, et que ce n'était pas la dernière,
                # la page suivante prend son index.
                # Si on a supprimé la dernière page (et qu'il en reste d'autres),
                # current_page_number doit pointer vers la nouvelle dernière page.
                if page_to_delete_index >= self.current_pdf_document.page_count:
                    self.current_page_number = self.current_pdf_document.page_count - 1

                # Dans tous les cas où il reste des pages, on rafraîchit.
                self.update_page_view() # Affichera la page à current_page_number (ou la nouvelle à cet index)
                self.update_thumbnails()
                self.update_navigation_controls()

            self.save_action.setEnabled(True) # Le document a été modifié

        except Exception as e:
            logging.error(f"Erreur lors de la suppression de la page {page_to_delete_index}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de suppression", f"Impossible de supprimer la page.\nErreur: {e}")
            # Il se peut que le document soit dans un état incohérent, recharger les miniatures
            self.update_thumbnails()

    def insert_blank_page(self):
        if not self.current_pdf_document:
            logging.warning("Tentative d'insertion de page sans document chargé.")
            QMessageBox.warning(self, "Aucun document", "Aucun document n'est ouvert pour y insérer une page.")
            return

        # Dialogue simple pour choisir où insérer et la taille (pour l'instant, taille de la page actuelle ou A4)
        # Pour simplifier cette étape, nous allons insérer après la page actuelle par défaut,
        # et utiliser les dimensions de la page actuelle si possible, sinon A4.

        page_to_insert_after = self.current_page_number # 0-indexed
        insert_at_index = page_to_insert_after + 1 # PyMuPDF insère *avant* cet index, donc +1 pour insérer après

        width, height = fitz.paper_size("a4") # Défaut A4 portrait
        if self.current_pdf_document.page_count > 0:
            try:
                # Essayer de prendre les dimensions de la page actuelle
                current_page_rect = self.current_pdf_document[self.current_page_number].rect
                width = current_page_rect.width
                height = current_page_rect.height
                logging.debug(f"Utilisation des dimensions de la page actuelle pour la nouvelle page: {width}x{height}")
            except Exception as e:
                logging.warning(f"Impossible d'obtenir les dimensions de la page actuelle, utilisation de A4 par défaut. Erreur: {e}")
        else: # Document vide, on insère la première page
            insert_at_index = 0


        # TODO: Créer un dialogue plus élaboré pour demander position, taille, orientation.
        # Pour l'instant : insérer après la page courante (ou au début si doc vide)
        # avec les dimensions de la page courante ou A4.

        confirm_msg = f"Insérer une page vierge après la page {page_to_insert_after + 1} (taille: {int(width)}x{int(height)}) ?"
        if self.current_pdf_document.page_count == 0:
            confirm_msg = f"Insérer une première page vierge (taille: {int(width)}x{int(height)}) ?"

        reply = QMessageBox.question(self, "Insérer Page Vierge", confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            logging.info(f"Tentative d'insertion d'une page vierge à l'index {insert_at_index} avec dimensions {width}x{height}.")
            # new_page(pno=-1, width=None, height=None)
            # pno: -1 pour ajouter à la fin, 0 pour insérer au début, N pour insérer avant la page N.
            self.current_pdf_document.new_page(pno=insert_at_index, width=width, height=height)
            self.is_document_modified = True
            logging.info(f"Page vierge insérée à l'index {insert_at_index}.")

            self.statusBar().showMessage(f"Page vierge insérée à la position {insert_at_index + 1}.")

            # Mettre à jour l'interface
            self.current_page_number = insert_at_index # Aller à la nouvelle page insérée
            self.update_page_view()
            self.update_thumbnails()
            self.update_navigation_controls()
            self.delete_page_action.setEnabled(True) # S'il y a au moins une page
            self.save_action.setEnabled(True)

        except Exception as e:
            logging.error(f"Erreur lors de l'insertion de la page vierge: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'insertion", f"Impossible d'insérer la page vierge.\nErreur: {e}")
            self.update_thumbnails() # Rafraîchir au cas où

    def import_pages_from_pdf(self):
        if not self.current_pdf_document:
            logging.warning("Tentative d'importation de pages sans document destination chargé.")
            QMessageBox.warning(self, "Aucun document destination", "Ouvrez ou créez d'abord un document PDF pour y importer des pages.")
            return

        source_file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner le PDF source pour l'importation", "", "Fichiers PDF (*.pdf)")
        if not source_file_path:
            return # L'utilisateur a annulé

        try:
            source_doc = fitz.open(source_file_path)
            if source_doc.page_count == 0:
                logging.info(f"Le PDF source '{source_file_path}' ne contient aucune page.")
                QMessageBox.information(self, "PDF Source Vide", f"Le fichier PDF source '{source_file_path}' est vide.")
                source_doc.close()
                return

            # Pour cette version simple : importer toutes les pages à la fin du document actuel.
            # TODO: Ajouter un dialogue pour sélectionner les pages sources et la position d'insertion.
            # PyMuPDF insert_pdf(docsrc, from_page=-1, to_page=-1, start_at=-1, ...)
            # start_at = -1 signifie insérer à la fin.

            num_pages_before_import = self.current_pdf_document.page_count
            insert_at_index = num_pages_before_import # Insérer après la dernière page actuelle

            logging.info(f"Tentative d'importation de {source_doc.page_count} pages depuis '{source_file_path}' à la fin du document actuel.")

            self.current_pdf_document.insert_pdf(source_doc) # Importe toutes les pages
            self.is_document_modified = True

            source_doc.close() # Fermer le document source après importation
            logging.info(f"{source_doc.page_count} pages importées avec succès.")
            self.statusBar().showMessage(f"{source_doc.page_count} pages importées depuis '{source_file_path}'.")

            # Mettre à jour l'interface
            # Aller à la première page importée
            self.current_page_number = insert_at_index
            self.update_page_view()
            self.update_thumbnails()
            self.update_navigation_controls()
            self.save_action.setEnabled(True)

        except Exception as e:
            logging.error(f"Erreur lors de l'importation de pages depuis '{source_file_path}': {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'importation", f"Impossible d'importer les pages depuis '{source_file_path}'.\nErreur: {e}")
            if 'source_doc' in locals() and source_doc.is_open:
                source_doc.close()
            self.update_thumbnails() # Rafraîchir au cas où l'état du doc actuel a changé

    def rotate_current_page(self, angle):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0:
            logging.warning("Tentative de rotation de page sans document ou page.")
            QMessageBox.warning(self, "Aucune page", "Aucune page à pivoter.")
            return

        if self.current_page_number < 0 or self.current_page_number >= self.current_pdf_document.page_count:
            logging.warning(f"Tentative de rotation d'une page invalide : {self.current_page_number}")
            return

        try:
            page = self.current_pdf_document[self.current_page_number]
            current_rotation = page.rotation
            new_rotation = (current_rotation + angle) % 360

            logging.info(f"Rotation de la page {self.current_page_number} de {angle}°. Rotation actuelle: {current_rotation}, Nouvelle: {new_rotation}")

            page.set_rotation(new_rotation) # PyMuPDF < 1.19.0 utilisait page.rotate = new_rotation
                                            # Pour les versions plus récentes, set_rotation est plus sûr/préféré.
                                            # Si fitz version est < 1.19.0, il faudra ajuster.
                                            # On assume une version récente de PyMuPDF.

            self.is_document_modified = True
            self.statusBar().showMessage(f"Page {self.current_page_number + 1} pivotée de {angle}°. Nouvelle rotation : {new_rotation}°")

            # Mettre à jour la vue principale et la miniature de la page affectée
            self.update_page_view()

            # Mettre à jour spécifiquement la miniature de la page tournée
            # Pour éviter de regénérer toutes les miniatures si ce n'est pas nécessaire.
            if 0 <= self.current_page_number < self.page_thumbnails_list.count():
                page_for_thumb = self.current_pdf_document.load_page(self.current_page_number)
                thumb_matrix = fitz.Matrix(0.2, 0.2)
                pix = page_for_thumb.get_pixmap(matrix=thumb_matrix) # La rotation est appliquée par get_pixmap
                image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
                pixmap = QPixmap.fromImage(qimage)

                list_item = self.page_thumbnails_list.item(self.current_page_number)
                if list_item:
                    list_item.setIcon(QIcon(pixmap))
            else: # Fallback si l'index est hors limites pour une raison quelconque
                self.update_thumbnails()


            self.save_action.setEnabled(True)

        except Exception as e:
            logging.error(f"Erreur lors de la rotation de la page {self.current_page_number}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de rotation", f"Impossible de pivoter la page.\nErreur: {e}")

    def crop_current_page(self):
        if not self.current_pdf_document or self.current_pdf_document.page_count == 0:
            QMessageBox.warning(self, "Aucune page", "Aucune page à rogner.")
            return

        page_index = self.current_page_number
        page = self.current_pdf_document[page_index]
        original_rect = page.rect # Ceci est le MediaBox, en points PDF (1/72 inch)

        logging.debug(f"Page {page_index} - Rectangle original (MediaBox): {original_rect}")

        # Créer un dialogue personnalisé pour entrer les valeurs de rognage
        # Pour l'instant, on va simuler cela avec des QInputDialog multiples, ce qui n'est pas idéal.
        # Un dialogue personnalisé avec 4 QSpinBox/QLineEdit serait mieux.

        # Les valeurs de rognage sont généralement relatives aux bords du MediaBox.
        # PyMuPDF attend un nouveau `fitz.Rect` pour `set_cropbox`.
        # Le CropBox définit la région visible de la page.

        # Exemple simple : demander de combien réduire chaque côté.
        # Pour une UI plus avancée, on demanderait x1, y1, x2, y2 du nouveau CropBox.

        # Pour cette implémentation initiale, on demande une simple réduction des marges.
        # On va supposer que l'utilisateur entre des valeurs en points PDF.

        # NOTE: Une meilleure approche serait un dialogue qui affiche les dimensions actuelles
        # et permet de spécifier soit le nouveau rectangle (x0,y0,x1,y1) soit des marges.
        # Pour l'instant, on va simplifier à l'extrême et demander un facteur de rognage.
        # Par exemple, réduire de 10% de chaque côté.

        # Utilisons QInputDialog pour un exemple simple : demander un nouveau rectangle (x0, y0, x1, y1)
        # sous forme de chaîne "x0 y0 x1 y1"

        current_cropbox = page.cropbox # Obtenir le cropbox actuel
        if not current_cropbox: # S'il n'y a pas de cropbox, il est égal au mediabox
            current_cropbox = original_rect

        rect_str, ok = QInputDialog.getText(self, "Rogner la Page",
                                              f"Page {page_index + 1} - Entrez le nouveau rectangle de rognage (x0 y0 x1 y1) "
                                              f"dans les coordonnées de la page (actuel: {current_cropbox.x0:.0f} {current_cropbox.y0:.0f} {current_cropbox.x1:.0f} {current_cropbox.y1:.0f}). "
                                              f"Le MediaBox est: {original_rect.x0:.0f} {original_rect.y0:.0f} {original_rect.x1:.0f} {original_rect.y1:.0f}.",
                                              QLineEdit.Normal,
                                              f"{current_cropbox.x0:.0f} {current_cropbox.y0:.0f} {current_cropbox.x1:.0f} {current_cropbox.y1:.0f}")
        if ok and rect_str:
            try:
                coords = list(map(float, rect_str.split()))
                if len(coords) != 4:
                    raise ValueError("Quatre coordonnées sont nécessaires.")

                new_crop_rect = fitz.Rect(coords[0], coords[1], coords[2], coords[3])

                # Valider le nouveau rectangle:
                # - Doit être dans les limites du MediaBox.
                # - x0 < x1 et y0 < y1.
                if not (original_rect.contains(new_crop_rect) and new_crop_rect.is_valid and not new_crop_rect.is_empty):
                    QMessageBox.warning(self, "Rectangle Invalide",
                                        "Le rectangle de rognage fourni est invalide ou en dehors des limites du MediaBox de la page.")
                    return

                logging.info(f"Rognage de la page {page_index} avec le rectangle: {new_crop_rect}")
                page.set_cropbox(new_crop_rect)
                self.is_document_modified = True
                self.statusBar().showMessage(f"Page {page_index + 1} rognée.")

                self.update_page_view()
                self.update_thumbnails() # Le rognage affecte l'apparence de la miniature
                self.save_action.setEnabled(True)

            except ValueError as ve:
                logging.warning(f"Valeur de rognage invalide: {rect_str} - {ve}")
                QMessageBox.warning(self, "Entrée Invalide", f"Format des coordonnées invalide : {ve}.\nUtilisez le format 'x0 y0 x1 y1'.")
            except Exception as e:
                logging.error(f"Erreur lors du rognage de la page {page_index}: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur de Rognage", f"Impossible de rogner la page.\nErreur: {e}")
        else:
            logging.debug("Opération de rognage annulée par l'utilisateur.")

    def toggle_highlight_mode(self, checked):
        if checked:
            logging.debug("Mode surlignage activé.")
            self.current_tool_mode = "highlight"
            self.statusBar().showMessage("Mode Surlignage Activé. Sélectionnez une zone à surligner.")
            # Potentiellement changer le curseur de la souris ici
            self.pdf_view.setCursor(Qt.CrossCursor)
            # Décocher les autres outils si d'autres modes existent plus tard
        else:
            logging.debug("Mode surlignage désactivé.")
            if self.current_tool_mode == "highlight": # S'assurer qu'on désactive le bon mode
                self.current_tool_mode = None
                self.statusBar().showMessage("Mode Surlignage Désactivé.")
                self.pdf_view.setCursor(Qt.ArrowCursor) # Curseur par défaut

    def graphics_view_mouse_press(self, event: QMouseEvent):
        if self.current_tool_mode == "highlight" and event.button() == Qt.LeftButton:
            self.selection_start_point = self.pdf_view.mapToScene(event.pos())
            logging.debug(f"Highlight mode: Mouse press at scene coords {self.selection_start_point}")

            # Initialiser le rectangle de sélection visuelle (temporaire)
            if self.selection_rect_item:
                self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None

            # Créer un rectangle transparent pour la sélection
            self.selection_rect_item = QGraphicsRectItem(QRectF(self.selection_start_point, self.selection_start_point))
            pen = QPen(Qt.DashLine)
            pen.setColor(Qt.black) # Couleur du contour du rectangle de sélection
            self.selection_rect_item.setPen(pen)
            # self.selection_rect_item.setBrush(QColor(0, 0, 255, 50)) # Remplissage bleu semi-transparent pour feedback
            self.pdf_scene.addItem(self.selection_rect_item)

        elif self.current_tool_mode == "pointer" and event.button() == Qt.LeftButton:
            self._clear_selected_annotation_feedback() # Effacer la sélection précédente
            scene_pos = self.pdf_view.mapToScene(event.pos())
            pdf_point = fitz.Point(scene_pos.x() / self.current_zoom_factor,
                                   scene_pos.y() / self.current_zoom_factor)

            if self.current_pdf_document and self.current_page_number >= 0:
                page = self.current_pdf_document.load_page(self.current_page_number)
                annot_found = None
                # Itérer sur les annotations de la page pour voir si le clic est dedans
                # On itère en sens inverse pour que les annotations du dessus soient prioritaires
                for annot in reversed(list(page.annots())):
                    if annot.rect.contains(pdf_point):
                        annot_found = annot
                        break

                if annot_found:
                    self.selected_annotation = annot_found
                    self.delete_selected_annot_action.setEnabled(True)
                    logging.info(f"Annotation sélectionnée: {annot_found}, type: {annot_found.type[1]}")
                    self.statusBar().showMessage(f"Annotation ({annot_found.type[1]}) sélectionnée.")

                    # Afficher un BBox autour de l'annotation sélectionnée
                    bbox_scene = QRectF(
                        annot_found.rect.x0 * self.current_zoom_factor,
                        annot_found.rect.y0 * self.current_zoom_factor,
                        annot_found.rect.width * self.current_zoom_factor,
                        annot_found.rect.height * self.current_zoom_factor
                    )
                    self.selected_annotation_bbox_item = QGraphicsRectItem(bbox_scene)
                    pen = QPen(Qt.blue, 2, Qt.DotLine) # Style pour la BBox de sélection
                    self.selected_annotation_bbox_item.setPen(pen)
                    self.pdf_scene.addItem(self.selected_annotation_bbox_item)
                else:
                    logging.debug("Aucune annotation trouvée au point de clic.")
                    self.statusBar().showMessage("Prêt.")


        elif self.current_tool_mode == "text_annot" and event.button() == Qt.LeftButton:
            self.selection_start_point = self.pdf_view.mapToScene(event.pos())
            logging.debug(f"Text Annot mode: Potential click at scene coords {self.selection_start_point}")

        elif self.current_tool_mode in ["rect_annot", "circle_annot", "line_annot"] and event.button() == Qt.LeftButton:
            self.selection_start_point = self.pdf_view.mapToScene(event.pos())
            logging.debug(f"{self.current_tool_mode} mode: Mouse press at scene coords {self.selection_start_point}")

            if self.selection_rect_item: # Nettoyer un éventuel rectangle/ligne de sélection précédent
                self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None

            # Pour rect et circle, on commence un QGraphicsRectItem. Pour line, un QGraphicsLineItem.
            if self.current_tool_mode in ["rect_annot", "circle_annot"]:
                self.selection_rect_item = QGraphicsRectItem(QRectF(self.selection_start_point, self.selection_start_point))
            elif self.current_tool_mode == "line_annot":
                self.selection_rect_item = QGraphicsLineItem(QLineF(self.selection_start_point, self.selection_start_point))

            if self.selection_rect_item:
                pen = QPen(QColor(int(self.shape_border_color[0]*255),
                                  int(self.shape_border_color[1]*255),
                                  int(self.shape_border_color[2]*255)))
                pen.setWidthF(self.shape_border_width * self.current_zoom_factor)
                pen.setStyle(Qt.DashLine)
                self.selection_rect_item.setPen(pen)
                self.pdf_scene.addItem(self.selection_rect_item)

        elif self.current_tool_mode == "ink" and event.button() == Qt.LeftButton:
            self.current_ink_stroke = [self.pdf_view.mapToScene(event.pos())]
            logging.debug(f"Ink mode: Mouse press, start stroke at {self.current_ink_stroke[0]}")

            # Pour le feedback visuel du tracé en cours
            if self.temp_ink_item:
                self.pdf_scene.removeItem(self.temp_ink_item)
            path = QPainterPath(self.current_ink_stroke[0])
            self.temp_ink_item = QGraphicsPathItem(path)
            pen = QPen(QColor(int(self.ink_color[0]*255), int(self.ink_color[1]*255), int(self.ink_color[2]*255)))
            pen.setWidthF(self.ink_thickness * self.current_zoom_factor) # Épaisseur ajustée au zoom pour le visuel
            self.temp_ink_item.setPen(pen)
            self.pdf_scene.addItem(self.temp_ink_item)

        else:
            # Passer l'événement au gestionnaire par défaut de QGraphicsView pour d'autres interactions (ex: drag scroll)
            super(QGraphicsView, self.pdf_view).mousePressEvent(event)


    def graphics_view_mouse_move(self, event: QMouseEvent):
        if self.current_tool_mode == "highlight" and self.selection_start_point:
            current_point = self.pdf_view.mapToScene(event.pos())
            if self.selection_rect_item:
                # Mettre à jour le rectangle de sélection visuelle
                rect = QRectF(self.selection_start_point, current_point).normalized()
                self.selection_rect_item.setRect(rect)

        elif self.current_tool_mode in ["rect_annot", "circle_annot"] and self.selection_start_point:
            current_point = self.pdf_view.mapToScene(event.pos())
            if self.selection_rect_item and isinstance(self.selection_rect_item, QGraphicsRectItem):
                rect = QRectF(self.selection_start_point, current_point).normalized()
                self.selection_rect_item.setRect(rect)

        elif self.current_tool_mode == "line_annot" and self.selection_start_point:
            current_point = self.pdf_view.mapToScene(event.pos())
            if self.selection_rect_item and isinstance(self.selection_rect_item, QGraphicsLineItem):
                line = QLineF(self.selection_start_point, current_point)
                self.selection_rect_item.setLine(line)

        # Pas de mouse_move spécifique pour "text_annot" car c'est un simple clic.

        elif self.current_tool_mode == "ink" and self.current_ink_stroke:
            current_point = self.pdf_view.mapToScene(event.pos())
            self.current_ink_stroke.append(current_point)

            # Mettre à jour le feedback visuel du tracé
            if self.temp_ink_item:
                path = QPainterPath(self.current_ink_stroke[0])
                for point in self.current_ink_stroke[1:]:
                    path.lineTo(point)
                self.temp_ink_item.setPath(path)
        else:
            super(QGraphicsView, self.pdf_view).mouseMoveEvent(event)

    def graphics_view_mouse_release(self, event: QMouseEvent):
        if self.current_tool_mode == "highlight" and self.selection_start_point and event.button() == Qt.LeftButton:
            end_point = self.pdf_view.mapToScene(event.pos())
            selection_rect_scene = QRectF(self.selection_start_point, end_point).normalized()
            logging.debug(f"Highlight mode: Mouse release. Selection rect in scene coords: {selection_rect_scene}")

            # Enlever le rectangle de sélection visuelle
            if self.selection_rect_item:
                self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None

            self.apply_highlight(selection_rect_scene)
            self.selection_start_point = None

        elif self.current_tool_mode == "rect_annot" and self.selection_start_point and event.button() == Qt.LeftButton:
            end_point = self.pdf_view.mapToScene(event.pos())
            selection_rect_scene = QRectF(self.selection_start_point, end_point).normalized()
            logging.debug(f"Rect Annot mode: Mouse release. Selection rect in scene coords: {selection_rect_scene}")
            if self.selection_rect_item:
                self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            self.apply_rect_annot(selection_rect_scene)
            self.selection_start_point = None

        elif self.current_tool_mode == "circle_annot" and self.selection_start_point and event.button() == Qt.LeftButton:
            end_point = self.pdf_view.mapToScene(event.pos())
            selection_rect_scene = QRectF(self.selection_start_point, end_point).normalized() # Rectangle englobant
            logging.debug(f"Circle Annot mode: Mouse release. Bounding rect in scene coords: {selection_rect_scene}")
            if self.selection_rect_item:
                self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            self.apply_circle_annot(selection_rect_scene)
            self.selection_start_point = None

        elif self.current_tool_mode == "line_annot" and self.selection_start_point and event.button() == Qt.LeftButton:
            end_point = self.pdf_view.mapToScene(event.pos())
            logging.debug(f"Line Annot mode: Mouse release. End point in scene coords: {end_point}")
            if self.selection_rect_item:
                self.pdf_scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = None
            self.apply_line_annot(self.selection_start_point, end_point)
            self.selection_start_point = None

        elif self.current_tool_mode == "text_annot" and self.selection_start_point and event.button() == Qt.LeftButton:
            # Vérifier si le point de relâchement est proche du point de pression (pour simuler un clic)
            end_point = self.pdf_view.mapToScene(event.pos())
            if (self.selection_start_point - end_point).manhattanLength() < 5: # Seuil pour un clic
                logging.debug(f"Text Annot mode: Click detected at scene coords {self.selection_start_point}")
                self.apply_text_annot(self.selection_start_point)
            else:
                logging.debug("Text Annot mode: Drag détecté, ignoré pour l'outil note (attente d'un clic).")
            self.selection_start_point = None # Réinitialiser dans tous les cas
            # L'outil reste actif pour ajouter d'autres notes jusqu'à ce qu'il soit désélectionné.

        elif self.current_tool_mode == "ink" and self.current_ink_stroke and event.button() == Qt.LeftButton:
            logging.debug(f"Ink mode: Mouse release, stroke finished with {len(self.current_ink_stroke)} points.")
            if self.temp_ink_item:
                self.pdf_scene.removeItem(self.temp_ink_item)
                self.temp_ink_item = None
            if len(self.current_ink_stroke) > 1:
                self.apply_ink(self.current_ink_stroke)
            self.current_ink_stroke = []

        else:
            super(QGraphicsView, self.pdf_view).mouseReleaseEvent(event)

    def apply_highlight(self, selection_rect_scene: QRectF):
        if not self.current_pdf_document or self.current_page_number < 0:
            return

        page = self.current_pdf_document.load_page(self.current_page_number)

        # Convertir les coordonnées de la scène (basées sur le pixmap zoomé) en coordonnées PDF
        # Le pixmap affiché est à self.pdf_view_item.pos() (typiquement 0,0 dans la scène si la scène est ajustée)
        # et a une mise à l'échelle de self.current_zoom_factor.

        # Coordonnées du rectangle de sélection par rapport au QGraphicsPixmapItem (qui est à 0,0 dans la scène)
        # Donc selection_rect_scene est déjà dans le système de coordonnées du pixmap.

        # Convertir en coordonnées PDF (non zoomées)
        pdf_x0 = selection_rect_scene.left() / self.current_zoom_factor
        pdf_y0 = selection_rect_scene.top() / self.current_zoom_factor
        pdf_x1 = selection_rect_scene.right() / self.current_zoom_factor
        pdf_y1 = selection_rect_scene.bottom() / self.current_zoom_factor

        highlight_rect_pdf = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)
        logging.info(f"Application du surlignage sur la page {self.current_page_number}, rect PDF: {highlight_rect_pdf}")

        try:
            # PyMuPDF attend une liste de Rects ou Quads pour add_highlight_annot.
            # Pour un simple rectangle, on peut l'utiliser directement.
            # Ou, pour être plus précis, on peut chercher le texte dans ce rectangle et surligner les quads du texte.

            # Approche 1: Surligner le rectangle entier (plus simple, moins précis pour le texte)
            # page.add_highlight_annot(highlight_rect_pdf)

            # Approche 2: Surligner le texte DANS le rectangle (plus précis)
            # text_instances = page.get_text("words", clip=highlight_rect_pdf) # Récupère les mots dans le rectangle
            # PyMuPDF `get_text("words")` renvoie (x0, y0, x1, y1, word, block_no, line_no, word_no)
            # On peut créer des annotations pour chaque mot, ou essayer de les grouper.
            # Pour un surlignage, on peut utiliser les 'quads' de surlignage.

            # PyMuPDF v1.18.0+ a `add_highlight_annot(quads=...)` ou `(rect)`
            # Pour un simple rectangle, on peut faire :
            annot = page.add_highlight_annot(highlight_rect_pdf)
            if annot: # Vérifier si l'annotation a été créée
                # Définir la couleur du surlignage
                # Les couleurs sont R, G, B, normalisées entre 0 et 1.
                annot.set_colors(stroke=self.highlight_color) # 'stroke' est la couleur pour highlight
                annot.update() # Appliquer les changements de couleur

                self.is_document_modified = True
                self.statusBar().showMessage(f"Zone surlignée sur la page {self.current_page_number + 1}.")

                # Rafraîchir la vue pour montrer le surlignage
                self.update_page_view()
                # La miniature doit aussi être mise à jour
                if 0 <= self.current_page_number < self.page_thumbnails_list.count():
                    list_item = self.page_thumbnails_list.item(self.current_page_number)
                    if list_item:
                        page_for_thumb = self.current_pdf_document.load_page(self.current_page_number)
                        thumb_matrix = fitz.Matrix(0.2, 0.2)
                        pix = page_for_thumb.get_pixmap(matrix=thumb_matrix)
                        image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
                        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
                        list_item.setIcon(QIcon(QPixmap.fromImage(qimage)))

                self.save_action.setEnabled(True)
            else:
                logging.warning("Impossible de créer l'annotation de surlignage.")
                QMessageBox.warning(self, "Surlignage", "Impossible de créer l'annotation de surlignage.")

        except Exception as e:
            logging.error(f"Erreur lors de l'application du surlignage: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de Surlignage", f"Impossible d'appliquer le surlignage.\nErreur: {e}")

    def toggle_ink_mode(self, checked):
        if checked:
            logging.debug("Mode Dessin (Stylo) activé.")
            self.current_tool_mode = "ink"
            self.highlight_action.setChecked(False) # Décocher les autres outils
            self.statusBar().showMessage("Mode Dessin Activé. Cliquez et dessinez sur la page.")
            self.pdf_view.setCursor(Qt.CrossCursor) # Ou un curseur de stylo si disponible
        else:
            logging.debug("Mode Dessin (Stylo) désactivé.")
            if self.current_tool_mode == "ink":
                self.current_tool_mode = None
                self.statusBar().showMessage("Mode Dessin Désactivé.")
                self.pdf_view.setCursor(Qt.ArrowCursor)

    def apply_ink(self, list_of_points_scene):
        if not self.current_pdf_document or self.current_page_number < 0 or not list_of_points_scene:
            return

        page = self.current_pdf_document.load_page(self.current_page_number)

        # Convertir les points de la scène en coordonnées PDF
        list_of_points_pdf = []
        for point in list_of_points_scene:
            pdf_x = point.x() / self.current_zoom_factor
            pdf_y = point.y() / self.current_zoom_factor
            list_of_points_pdf.append(fitz.Point(pdf_x, pdf_y))

        if not list_of_points_pdf:
            logging.warning("Aucun point à dessiner pour l'annotation d'encre.")
            return

        logging.info(f"Application du dessin sur la page {self.current_page_number} avec {len(list_of_points_pdf)} points.")

        try:
            # PyMuPDF attend une liste de listes de points (chaque sous-liste est un trait continu)
            annot = page.add_ink_annot([list_of_points_pdf])
            if annot:
                annot.set_colors(stroke=self.ink_color) # 'stroke' est la couleur pour ink
                annot.set_line_width(self.ink_thickness)
                annot.update(blend_mode="Darken") # Mode de fusion optionnel

                self.is_document_modified = True
                self.statusBar().showMessage(f"Dessin ajouté à la page {self.current_page_number + 1}.")

                self.update_page_view() # Rafraîchir pour voir le dessin
                if 0 <= self.current_page_number < self.page_thumbnails_list.count(): # Mettre à jour miniature
                    list_item = self.page_thumbnails_list.item(self.current_page_number)
                    if list_item:
                        page_for_thumb = self.current_pdf_document.load_page(self.current_page_number)
                        thumb_matrix = fitz.Matrix(0.2, 0.2)
                        pix = page_for_thumb.get_pixmap(matrix=thumb_matrix)
                        image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
                        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
                        list_item.setIcon(QIcon(QPixmap.fromImage(qimage)))

                self.save_action.setEnabled(True)
            else:
                logging.warning("Impossible de créer l'annotation d'encre.")
                QMessageBox.warning(self, "Dessin", "Impossible de créer l'annotation de dessin.")

        except Exception as e:
            logging.error(f"Erreur lors de l'application du dessin: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de Dessin", f"Impossible d'appliquer le dessin.\nErreur: {e}")

    def toggle_rect_annot_mode(self, checked):
        if checked:
            logging.debug("Mode Dessin Rectangle activé.")
            self.current_tool_mode = "rect_annot"
            self.highlight_action.setChecked(False)
            self.ink_action.setChecked(False)
            self.statusBar().showMessage("Mode Dessin Rectangle Activé. Cliquez et dessinez un rectangle.")
            self.pdf_view.setCursor(Qt.CrossCursor)
        else:
            logging.debug("Mode Dessin Rectangle désactivé.")
            if self.current_tool_mode == "rect_annot":
                self.current_tool_mode = None
                self.statusBar().showMessage("Mode Dessin Rectangle Désactivé.")
                self.pdf_view.setCursor(Qt.ArrowCursor)

    def apply_rect_annot(self, selection_rect_scene: QRectF):
        if not self.current_pdf_document or self.current_page_number < 0:
            return

        page = self.current_pdf_document.load_page(self.current_page_number)

        pdf_x0 = selection_rect_scene.left() / self.current_zoom_factor
        pdf_y0 = selection_rect_scene.top() / self.current_zoom_factor
        pdf_x1 = selection_rect_scene.right() / self.current_zoom_factor
        pdf_y1 = selection_rect_scene.bottom() / self.current_zoom_factor

        rect_annot_pdf = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)
        logging.info(f"Application de l'annotation Rectangle sur la page {self.current_page_number}, rect PDF: {rect_annot_pdf}")

        try:
            annot = page.add_rect_annot(rect_annot_pdf)
            if annot:
                annot.set_colors(stroke=self.shape_border_color, fill=self.shape_fill_color)
                annot.set_border(width=self.shape_border_width)
                # annot.set_opacity(0.5) # Si on veut de la transparence pour le remplissage
                annot.update()

                self.is_document_modified = True
                self.statusBar().showMessage(f"Rectangle ajouté à la page {self.current_page_number + 1}.")
                self.update_page_view()
                if 0 <= self.current_page_number < self.page_thumbnails_list.count():
                    list_item = self.page_thumbnails_list.item(self.current_page_number)
                    if list_item:
                        page_for_thumb = self.current_pdf_document.load_page(self.current_page_number)
                        thumb_matrix = fitz.Matrix(0.2, 0.2)
                        pix = page_for_thumb.get_pixmap(matrix=thumb_matrix)
                        image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
                        qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
                        list_item.setIcon(QIcon(QPixmap.fromImage(qimage)))
                self.save_action.setEnabled(True)
            else:
                logging.warning("Impossible de créer l'annotation Rectangle.")
                QMessageBox.warning(self, "Dessin Rectangle", "Impossible de créer l'annotation Rectangle.")
        except Exception as e:
            logging.error(f"Erreur lors de l'application de l'annotation Rectangle: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Dessin Rectangle", f"Impossible d'appliquer l'annotation Rectangle.\nErreur: {e}")

    def toggle_circle_annot_mode(self, checked):
        if checked:
            self.current_tool_mode = "circle_annot"
            self._update_tool_mode_ui("Dessin Cercle/Ellipse")
            self.highlight_action.setChecked(False)
            self.ink_action.setChecked(False)
            self.rect_annot_action.setChecked(False)
            self.line_annot_action.setChecked(False)
        elif self.current_tool_mode == "circle_annot":
            self._update_tool_mode_ui(None)

    def toggle_line_annot_mode(self, checked):
        if checked:
            self.current_tool_mode = "line_annot"
            self._update_tool_mode_ui("Dessin Ligne")
            self.highlight_action.setChecked(False)
            self.ink_action.setChecked(False)
            self.rect_annot_action.setChecked(False)
            self.circle_annot_action.setChecked(False)
        elif self.current_tool_mode == "line_annot":
            self._update_tool_mode_ui(None)

    def _update_tool_mode_ui(self, mode_name=None):
        """Met à jour l'interface utilisateur en fonction du mode outil."""
        if mode_name:
            logging.debug(f"Mode {mode_name} activé.")
            self.statusBar().showMessage(f"Mode {mode_name} Activé. Cliquez et dessinez.")
            self.pdf_view.setCursor(Qt.CrossCursor)
        else:
            logging.debug("Aucun mode outil spécifique activé.")
            self.current_tool_mode = None
            self.statusBar().showMessage("Prêt.")
            self.pdf_view.setCursor(Qt.ArrowCursor)

    def apply_circle_annot(self, selection_rect_scene: QRectF):
        if not self.current_pdf_document or self.current_page_number < 0: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_rect = fitz.Rect(
            selection_rect_scene.left() / self.current_zoom_factor,
            selection_rect_scene.top() / self.current_zoom_factor,
            selection_rect_scene.right() / self.current_zoom_factor,
            selection_rect_scene.bottom() / self.current_zoom_factor
        )
        logging.info(f"Ajout Cercle/Ellipse sur page {self.current_page_number}, rect PDF: {pdf_rect}")
        try:
            annot = page.add_circle_annot(pdf_rect)
            if annot:
                annot.set_colors(stroke=self.shape_border_color, fill=self.shape_fill_color)
                annot.set_border(width=self.shape_border_width)
                annot.update()
                self.is_document_modified = True
                self.statusBar().showMessage(f"Cercle/Ellipse ajouté à la page {self.current_page_number + 1}.")
                self._refresh_page_and_thumbnail()
            else: QMessageBox.warning(self, "Dessin Cercle", "Impossible de créer l'annotation Cercle.")
        except Exception as e:
            logging.error(f"Erreur annotation Cercle: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Dessin Cercle", f"Erreur: {e}")

    def apply_line_annot(self, p1_scene: QPointF, p2_scene: QPointF):
        if not self.current_pdf_document or self.current_page_number < 0: return
        page = self.current_pdf_document.load_page(self.current_page_number)
        p1_pdf = fitz.Point(p1_scene.x() / self.current_zoom_factor, p1_scene.y() / self.current_zoom_factor)
        p2_pdf = fitz.Point(p2_scene.x() / self.current_zoom_factor, p2_scene.y() / self.current_zoom_factor)
        logging.info(f"Ajout Ligne sur page {self.current_page_number}, de {p1_pdf} à {p2_pdf}")
        try:
            annot = page.add_line_annot(p1_pdf, p2_pdf)
            if annot:
                annot.set_colors(stroke=self.shape_border_color) # Ligne n'a pas de 'fill'
                annot.set_border(width=self.shape_border_width)
                # On peut ajouter des pointes de flèches ici si désiré: annot.set_line_ends(fitz.LINE_END_CLOSEDARROW, fitz.LINE_END_NONE)
                annot.update()
                self.is_document_modified = True
                self.statusBar().showMessage(f"Ligne ajoutée à la page {self.current_page_number + 1}.")
                self._refresh_page_and_thumbnail()
            else: QMessageBox.warning(self, "Dessin Ligne", "Impossible de créer l'annotation Ligne.")
        except Exception as e:
            logging.error(f"Erreur annotation Ligne: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Dessin Ligne", f"Erreur: {e}")

    def toggle_text_annot_mode(self, checked):
        if checked:
            self.current_tool_mode = "text_annot"
            self._update_tool_mode_ui("Ajout de Note Textuelle")
            # Décocher les autres outils d'annotation
            self.highlight_action.setChecked(False)
            self.ink_action.setChecked(False)
            self.rect_annot_action.setChecked(False)
            self.circle_annot_action.setChecked(False)
            self.line_annot_action.setChecked(False)
            self.text_annot_action.setChecked(False) # Décocher aussi l'outil note
            self.pdf_view.setCursor(Qt.PointingHandCursor)
        elif self.current_tool_mode == "text_annot":
            self._update_tool_mode_ui(None)

    def _deselect_all_tool_actions(self):
        """Décoche toutes les actions d'outils d'annotation."""
        self.highlight_action.setChecked(False)
        self.ink_action.setChecked(False)
        self.rect_annot_action.setChecked(False)
        self.circle_annot_action.setChecked(False)
        self.line_annot_action.setChecked(False)
        self.text_annot_action.setChecked(False)
        # self.current_tool_mode = None # Est fait par _update_tool_mode_ui(None)

    def _update_tool_mode_ui(self, mode_name=None):
        """Met à jour l'interface utilisateur en fonction du mode outil."""
        if mode_name:
            logging.debug(f"Mode {mode_name} activé.")
            self.statusBar().showMessage(f"Mode {mode_name} Activé. Interagissez avec la page.")
            if mode_name == "text_annot":
                 self.pdf_view.setCursor(Qt.PointingHandCursor)
            else:
                 self.pdf_view.setCursor(Qt.CrossCursor)
            self._clear_selected_annotation_feedback() # Effacer la sélection d'annotation précédente
        else: # Aucun mode outil spécifique, on passe en mode Pointeur/Sélection par défaut
            logging.debug("Mode Pointeur/Sélection activé (aucun outil d'annotation spécifique).")
            self.current_tool_mode = "pointer" # Mode par défaut pour sélectionner des annotations
            self.statusBar().showMessage("Prêt. Cliquez pour sélectionner une annotation.")
            self.pdf_view.setCursor(Qt.ArrowCursor)


    def apply_text_annot(self, point_scene: QPointF):
        if not self.current_pdf_document or self.current_page_number < 0: return

        text, ok = QInputDialog.getMultiLineText(self, "Ajouter une Note", "Entrez le texte de votre note :")

        # Important: après le dialogue, s'assurer que le mode est bien désactivé si l'utilisateur a annulé
        # ou si l'action est terminée, pour revenir au mode pointeur.
        is_tool_still_active = self.text_annot_action.isChecked()

        if not (ok and text.strip()):
            logging.debug("Ajout de note annulé ou texte vide.")
            if is_tool_still_active: # Si l'outil était encore coché
                self.text_annot_action.setChecked(False) # Déclenche toggle_text_annot_mode(False) -> _update_tool_mode_ui(None)
            elif self.current_tool_mode == "text_annot": # Si décoché par un autre moyen mais mode encore actif
                 self._update_tool_mode_ui(None)
            return

        page = self.current_pdf_document.load_page(self.current_page_number)
        pdf_point = fitz.Point(point_scene.x() / self.current_zoom_factor,
                               point_scene.y() / self.current_zoom_factor)
        logging.info(f"Ajout d'une note textuelle à la page {self.current_page_number} au point PDF: {pdf_point}")

        try:
            annot = page.add_text_annot(pdf_point, text)
            if annot:
                annot.set_info(content=text)
                annot.update()
                self.is_document_modified = True
                self.statusBar().showMessage(f"Note textuelle ajoutée à la page {self.current_page_number + 1}.")
                self._refresh_page_and_thumbnail()
            else:
                QMessageBox.warning(self, "Ajout de Note", "Impossible de créer l'annotation textuelle.")
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de la note textuelle: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur d'Annotation", f"Impossible d'ajouter la note textuelle.\nErreur: {e}")

        if is_tool_still_active: # Désactiver l'outil après une action réussie
            self.text_annot_action.setChecked(False)
        elif self.current_tool_mode == "text_annot": # Au cas où
             self._update_tool_mode_ui(None)

    def _clear_selected_annotation_feedback(self):
        if self.selected_annotation_bbox_item:
            self.pdf_scene.removeItem(self.selected_annotation_bbox_item)
            self.selected_annotation_bbox_item = None
        self.selected_annotation = None
        self.delete_selected_annot_action.setEnabled(False)

    def delete_selected_annotation(self):
        if not self.selected_annotation:
            QMessageBox.information(self, "Aucune sélection", "Aucune annotation n'est sélectionnée pour la suppression.")
            return

        if not self.current_pdf_document or self.current_page_number < 0: return

        page = self.current_pdf_document.load_page(self.current_page_number)
        try:
            logging.info(f"Suppression de l'annotation: {self.selected_annotation}")
            page.delete_annot(self.selected_annotation)
            self.is_document_modified = True
            self.statusBar().showMessage("Annotation supprimée.")
            self._clear_selected_annotation_feedback()
            self._refresh_page_and_thumbnail()
        except Exception as e:
            logging.error(f"Erreur lors de la suppression de l'annotation: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de Suppression", f"Impossible de supprimer l'annotation.\nErreur: {e}")


    def _refresh_page_and_thumbnail(self):
        """Helper pour rafraîchir la vue de la page et sa miniature."""
        self.update_page_view()
        if 0 <= self.current_page_number < self.page_thumbnails_list.count():
            list_item = self.page_thumbnails_list.item(self.current_page_number)
            if list_item:
                page_for_thumb = self.current_pdf_document.load_page(self.current_page_number)
                thumb_matrix = fitz.Matrix(0.2, 0.2)
                pix = page_for_thumb.get_pixmap(matrix=thumb_matrix)
                image_format = QImage.Format_RGB888 if pix.alpha == 0 else QImage.Format_RGBA8888
                qimage = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
                list_item.setIcon(QIcon(QPixmap.fromImage(qimage)))
        self.save_action.setEnabled(True)



    # S'assurer que open_file demande aussi avant d'écraser un doc ouvert
    def open_file(self): # Redéfinition pour inclure _ask_save_before_action
        if not self._ask_save_before_action():
            return # L'utilisateur a annulé l'ouverture

        # Si un document était ouvert, il est maintenant (potentiellement) sauvegardé ou ignoré.
        # On peut le fermer proprement avant d'en ouvrir un nouveau.
        if self.current_pdf_document:
            try:
                self.current_pdf_document.close()
                logging.debug("Ancien document fermé avant d'en ouvrir un nouveau.")
            except Exception as e:
                logging.warning(f"Erreur à la fermeture de l'ancien document: {e}")
            self.current_pdf_document = None
            self._reset_ui_on_error() # Réinitialise l'UI pour le nouveau fichier


        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier PDF", "", "Fichiers PDF (*.pdf);;Tous les fichiers (*)")
        if file_path:
            try:
                self.current_pdf_document = fitz.open(file_path)
                self.current_page_number = 0
                self.current_zoom_factor = 1.0
                self.is_document_modified = False
                self.update_page_view()
                self.update_thumbnails()
                self.update_navigation_controls()
                self.save_action.setEnabled(True)
                self.save_as_action.setEnabled(True)
                self.zoom_in_action.setEnabled(True)
                self.zoom_out_action.setEnabled(True)
                self.zoom_original_action.setEnabled(True)
                self.delete_page_action.setEnabled(True)
                self.insert_blank_page_action.setEnabled(True)
                self.import_pages_action.setEnabled(True)
                self.rotate_cw_action.setEnabled(True)
                self.rotate_ccw_action.setEnabled(True)
                self.crop_page_action.setEnabled(True)
                self.highlight_action.setEnabled(True)
                self.ink_action.setEnabled(True)
                self.rect_annot_action.setEnabled(True)
                self.circle_annot_action.setEnabled(True)
                self.line_annot_action.setEnabled(True)
                self.text_annot_action.setEnabled(True) # Activer ajout de note
                self.statusBar().showMessage(f"Ouvert : {file_path}")
                logging.info(f"Fichier PDF ouvert : {file_path}")
                self.setWindowTitle(f"Éditeur PDF PyQt - Page {self.current_page_number + 1}/{self.current_pdf_document.page_count} [{file_path}]")

            except Exception as e:
                logging.error(f"Erreur lors de l'ouverture du PDF {file_path}: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur d'ouverture", f"Impossible d'ouvrir le fichier PDF '{file_path}'.\nErreur : {e}")
                self.current_pdf_document = None
                self._reset_ui_on_error()


if __name__ == '__main__':
    # Configuration du logging déplacée au niveau du module pour être active dès le début.
    app = QApplication(sys.argv)
    # Pour les icônes, si on a un fichier resources.qrc compilé en, par exemple, resources_rc.py:
    # try:
    #     import resources_rc  # Importer le fichier de ressources compilé
    # except ImportError:
    #     print("Note: Fichier de ressources (resources_rc.py) non trouvé. Les icônes pourraient manquer.")
    #     # On peut continuer sans, QIcon.fromTheme tentera de trouver des icônes système.
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
