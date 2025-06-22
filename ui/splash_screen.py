import os
import random
import logging
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QMovie, QFont, QPalette, QColor, QBrush
from PyQt5.QtCore import Qt, QSize, QTimer

class SplashWindow(QWidget):
    def __init__(self, app_root_dir):
        super().__init__()
        self.app_root_dir = app_root_dir
        self.default_static_pixmap = QPixmap(os.path.join(self.app_root_dir, "icons", "leopard_logo.svg"))
        
        # Configure window properties for splash-like behavior
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool) # Qt.Tool helps it float like a splash
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        
        # Ensure the widget itself has a transparent background style
        self.setStyleSheet("QWidget { background-color: transparent; }")

        self.gif_movie = None # To keep QMovie instance alive

        self._setup_ui()

    def _get_random_motivational_message(self):
        motivational_messages = [
            "Chaque jour est une nouvelle opportunité.", "Croyez en vous et tout deviendra possible.",
            "Le succès commence par un état d'esprit.", "Soyez le changement que vous voulez voir.",
            "La persévérance est la clé.", "N'ayez peur de ne pas essayer.",
            "Le futur appartient aux rêveurs."
        ]
        return random.choice(motivational_messages)

    def _get_random_gif_path(self):
        gif_folder = os.path.join(self.app_root_dir, "resources", "gifs")
        if os.path.isdir(gif_folder):
            gif_files = [f for f in os.listdir(gif_folder) if f.lower().endswith(".gif")]
            if gif_files:
                return os.path.join(gif_folder, random.choice(gif_files))
        logging.warning(f"No GIF files in {gif_folder} or folder missing.")
        return None

    def _setup_ui(self):
        selected_message = self._get_random_motivational_message()
        selected_gif_path = self._get_random_gif_path()

        main_layout = QVBoxLayout(self) # Set layout directly on the SplashWindow (self)
        main_layout.setContentsMargins(20, 20, 20, 20) # Generous margins for content
        main_layout.setAlignment(Qt.AlignCenter)

        # Message Label
        self.message_label = QLabel(selected_message, self)
        self.message_label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel { 
                color: white; 
                font-size: 20px; 
                font-weight: bold; 
                background-color: rgba(0, 0, 0, 0.0); /* Fully transparent background for label itself */
                padding: 10px; 
                text-align: center; 
            }
        """)
        # To avoid text repainting issues, ensure labels don't auto-fill their background
        self.message_label.setAutoFillBackground(False)
        self.message_label.setAttribute(Qt.WA_TranslucentBackground, True)
        main_layout.addWidget(self.message_label)

        # Media Label (for GIF or static image)
        self.media_label = QLabel(self)
        self.media_label.setAlignment(Qt.AlignCenter)
        self.media_label.setAutoFillBackground(False)
        self.media_label.setAttribute(Qt.WA_TranslucentBackground, True)
        main_layout.addWidget(self.media_label, 1) # Stretch factor

        MAX_MEDIA_WIDTH = 500
        MAX_MEDIA_HEIGHT = 380
        DEFAULT_MEDIA_WIDTH = 300
        DEFAULT_MEDIA_HEIGHT = 220
        target_media_width = DEFAULT_MEDIA_WIDTH
        target_media_height = DEFAULT_MEDIA_HEIGHT

        if selected_gif_path:
            self.gif_movie = QMovie(selected_gif_path)
            if self.gif_movie.isValid():
                original_size = self.gif_movie.currentPixmap().size()
                if original_size.isValid() and not original_size.isEmpty():
                    target_media_width, target_media_height = self._calculate_scaled_dimensions(
                        original_size, MAX_MEDIA_WIDTH, MAX_MEDIA_HEIGHT
                    )
                self.gif_movie.setScaledSize(QSize(target_media_width, target_media_height))
                self.media_label.setMovie(self.gif_movie)
                self.gif_movie.start()
                # Connect frameChanged to ensure the label updates, might help with text rendering
                self.gif_movie.frameChanged.connect(self._on_gif_frame_changed)
            else:
                logging.error(f"Invalid QMovie for {selected_gif_path}. Using static fallback.")
                self._set_static_media_pixmap(DEFAULT_MEDIA_WIDTH, DEFAULT_MEDIA_HEIGHT)
        else:
            self._set_static_media_pixmap(DEFAULT_MEDIA_WIDTH, DEFAULT_MEDIA_HEIGHT)
        
        self.media_label.setFixedSize(target_media_width, target_media_height)
        self.message_label.setFixedWidth(target_media_width) # Match message width to media

        # Adjust overall window size based on content
        # The layout will manage the overall size of the QWidget (self)
        self.adjustSize() # Adjusts window to layout's preferred size

    def _on_gif_frame_changed(self, frame_number):
        # This slot is called when the GIF frame changes.
        # We might need to explicitly update the message label if text artifacts appear.
        # self.message_label.update() # Try this if text artifacts persist.
        # It's also possible the issue is with how the QMovie updates the QLabel.
        # The QLabel hosting the QMovie should repaint correctly.
        # If the issue is text overdrawing, it's more likely related to the message_label's updates.
        pass


    def _calculate_scaled_dimensions(self, original_size, max_w, max_h):
        img_w = original_size.width()
        img_h = original_size.height()
        aspect = img_w / img_h if img_h > 0 else 1.0

        scaled_w, scaled_h = img_w, img_h
        if scaled_w > max_w:
            scaled_w = max_w
            scaled_h = int(scaled_w / aspect)
        if scaled_h > max_h:
            scaled_h = max_h
            scaled_w = int(scaled_h * aspect)
        return scaled_w, scaled_h

    def _set_static_media_pixmap(self, width, height):
        pix = self.default_static_pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.media_label.setPixmap(pix)

    def show_splash(self):
        self.show()
        self._center_on_screen()
        QApplication.instance().processEvents()

    def _center_on_screen(self):
        screen_geo = QApplication.instance().desktop().availableGeometry(self)
        self.move(screen_geo.center() - self.rect().center())

    def finish_splash(self, main_window):
        # main_window is passed but not strictly needed for QWidget.hide/close
        self.hide() # or self.close() to destroy
        # If self.close() is used, ensure QMovie is stopped if running
        if self.gif_movie:
            self.gif_movie.stop()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    # Assuming script is in ui/ and resources/ & icons/ are in parent dir
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    splash = SplashWindow(app_root_dir=project_root)
    splash.show_splash()
    
    # Simulate app loading and main window appearance
    main_win_dummy = QWidget() # Dummy main window for finish_splash
    QTimer.singleShot(6000, lambda: splash.finish_splash(main_win_dummy)) # Show for 6s
    QTimer.singleShot(6500, app.quit) # Quit app shortly after splash closes

    sys.exit(app.exec_())
