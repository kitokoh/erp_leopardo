# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QSizePolicy, QSpinBox, QWidget,
    QScrollArea, QApplication, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QRectF, QCoreApplication


class PdfViewerWidget(QDialog):
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.current_pdf_document = None
        self.current_page_number = 0
        self.current_zoom_factor = 1.0 # Default zoom
        self.current_view_rotation_angle = 0 # Angle de rotation actuel de la vue

        # Utilisation de self.tr() pour le titre de la fenêtre
        self.setWindowTitle(self.tr("Visionneuse PDF - {0}").format(pdf_path))
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self._setup_ui()
        self._load_pdf()

    def tr(self, text, disambiguation=None, n=-1):
        # Helper pour la traduction, s'assurant que QCoreApplication.translate est utilisé
        # avec le contexte de cette classe.
        return QCoreApplication.translate("PdfViewerWidget", text, disambiguation, n)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Controls Layout
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)

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

        main_layout.addWidget(controls_widget)

        # PDF View Area
        self.pdf_view = QGraphicsView(self)
        self.pdf_scene = QGraphicsScene(self)
        self.pdf_view.setScene(self.pdf_scene)
        self.pdf_view_item = QGraphicsPixmapItem()
        self.pdf_scene.addItem(self.pdf_view_item)

        # Use QScrollArea for better handling if PDF is larger than view
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.pdf_view)
        main_layout.addWidget(scroll_area) # Add scroll_area instead of pdf_view directly

        # Close button
        close_button = QPushButton(QIcon.fromTheme("window-close", QIcon(":/icons/x-circle.svg")), self.tr("Fermer"))
        close_button.setToolTip(self.tr("Fermer la visionneuse"))
        close_button.clicked.connect(self.accept)

        button_bar_layout = QHBoxLayout()
        button_bar_layout.addStretch()
        button_bar_layout.addWidget(close_button)
        main_layout.addLayout(button_bar_layout)


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
            else:
                self.total_pages_label.setText(self.tr("Document vide"))
                self._disable_all_controls()
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture du PDF '{self.pdf_path}': {e}", exc_info=True)
            self.total_pages_label.setText(self.tr("Erreur: {0}").format(str(e)))
            self._disable_all_controls()
            QMessageBox.critical(self, self.tr("Erreur PDF"),
                                 self.tr("Impossible d'ouvrir le fichier PDF '{0}'.\nErreur: {1}").format(self.pdf_path, str(e)))


    def update_page_view(self):
        if not self.current_pdf_document or \
           self.current_page_number < 0 or \
           self.current_page_number >= self.current_pdf_document.page_count:
            self.pdf_scene.clear() # Clear the scene if no valid page
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
                self.update_page_view()
                self.update_navigation_controls()

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
