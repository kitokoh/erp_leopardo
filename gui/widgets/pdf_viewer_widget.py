# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QSizePolicy, QSpinBox, QWidget,
    QScrollArea, QApplication
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QRectF


class PdfViewerWidget(QDialog):
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.current_pdf_document = None
        self.current_page_number = 0
        self.current_zoom_factor = 1.0 # Default zoom

        self.setWindowTitle(f"Visionneuse PDF - {pdf_path}")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self._setup_ui()
        self._load_pdf()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Controls Layout
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        self.prev_page_button = QPushButton(QIcon.fromTheme("go-previous", QIcon(":/icons/arrow-left-circle.svg")), "< Préc.")
        self.prev_page_button.clicked.connect(self.go_to_previous_page)
        self.prev_page_button.setEnabled(False)
        controls_layout.addWidget(self.prev_page_button)

        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.setEnabled(False)
        self.page_spinbox.valueChanged.connect(self.go_to_page_from_spinbox)
        controls_layout.addWidget(self.page_spinbox)

        self.total_pages_label = QLabel("/ N/A")
        controls_layout.addWidget(self.total_pages_label)

        self.next_page_button = QPushButton(QIcon.fromTheme("go-next", QIcon(":/icons/arrow-right-circle.svg")), "Suiv. >")
        self.next_page_button.clicked.connect(self.go_to_next_page)
        self.next_page_button.setEnabled(False)
        controls_layout.addWidget(self.next_page_button)

        controls_layout.addStretch()

        self.zoom_out_button = QPushButton(QIcon.fromTheme("zoom-out", QIcon(":/icons/zoom-out.svg")), "Zoom -")
        self.zoom_out_button.clicked.connect(lambda: self.zoom(0.9))
        self.zoom_out_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_out_button)

        self.zoom_in_button = QPushButton(QIcon.fromTheme("zoom-in", QIcon(":/icons/zoom-in.svg")), "Zoom +")
        self.zoom_in_button.clicked.connect(lambda: self.zoom(1.1))
        self.zoom_in_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_in_button)

        self.zoom_original_button = QPushButton(QIcon.fromTheme("zoom-original", QIcon(":/icons/zoom-original.svg")), "Zoom 100%")
        self.zoom_original_button.clicked.connect(lambda: self.set_zoom_factor(1.0))
        self.zoom_original_button.setEnabled(False)
        controls_layout.addWidget(self.zoom_original_button)


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
        close_button = QPushButton(QIcon.fromTheme("window-close", QIcon(":/icons/x-circle.svg")), "Fermer")
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
            else:
                self.total_pages_label.setText("Document vide")
                self._disable_all_controls()
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture du PDF '{self.pdf_path}': {e}", exc_info=True)
            self.total_pages_label.setText(f"Erreur: {e}")
            self._disable_all_controls()
            # Consider showing a QMessageBox here as well.
            QMessageBox.critical(self, "Erreur PDF", f"Impossible d'ouvrir le fichier PDF '{self.pdf_path}'.\nErreur: {e}")


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
            matrix = fitz.Matrix(self.current_zoom_factor, self.current_zoom_factor)
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
        if not self.total_pages_label.text().startswith("Erreur"):
             self.total_pages_label.setText("/ N/A")


    def go_to_page(self, page_num_zero_indexed):
        if self.current_pdf_document and 0 <= page_num_zero_indexed < self.current_pdf_document.page_count:
            if self.current_page_number != page_num_zero_indexed:
                self.current_page_number = page_num_zero_indexed
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
