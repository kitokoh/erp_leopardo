import os
import random
import logging
import datetime # Added for day_of_year calculation

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QMovie, QFont, QPalette, QColor, QBrush
from PyQt5.QtCore import Qt, QSize, QTimer, QLocale, QPropertyAnimation, QEasingCurve, pyqtProperty

# Assuming db connection and GenericCRUD are accessible
# This might require adjusting imports based on your project structure
# For example, if db.cruds.generic_crud is the path:

from db.connection import get_db_connection # Corrected import
from db.cruds.generic_crud import GenericCRUD


class SplashWindow(QWidget):
    def __init__(self, app_root_dir, language_code=None):
        super().__init__()
        self.app_root_dir = app_root_dir
        self.language_code = language_code or QLocale.system().name().split('_')[0] # e.g., 'en', 'fr'
        self.default_static_pixmap = QPixmap(os.path.join(self.app_root_dir, "icons", "leopard_logo.svg"))

        # Configure window properties for splash-like behavior
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool) # Qt.Tool helps it float like a splash
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        # Ensure the widget itself has a transparent background style
        self.setStyleSheet("QWidget { background-color: transparent; }")

        self.gif_movie = None # To keep QMovie instance alive
        self.animation = None # For fade animations

        self._setup_ui()
        self.setWindowOpacity(0.0) # Start fully transparent for fade-in

    def _get_random_motivational_message(self):
        conn = None
        try:
            conn = get_db_connection()
            messages_crud = GenericCRUD(table_name='motivational_messages', primary_key='id')

            current_day_of_year = datetime.date.today().timetuple().tm_yday

            conn = get_db_connection()

            # Pool for all potential messages
            candidate_messages = []

            # 1. Fetch User-Customized Messages (prioritize these)
            # These are considered general purpose for now, not tied to day_of_year
            user_messages_crud = GenericCRUD(conn, 'user_motivational_messages', 'id')
            # Fetch user messages for current language OR language_code IS NULL (language-neutral)
            user_lang_specific = user_messages_crud.get_by_attributes(
                {"language_code": self.language_code, "is_active": True}
            )
            user_lang_neutral = user_messages_crud.get_by_attributes(
                {"language_code": None, "is_active": True} # Assuming NULL language_code for neutral
            )
            if user_lang_specific:
                candidate_messages.extend([m['message'] for m in user_lang_specific])
            if user_lang_neutral:
                candidate_messages.extend([m['message'] for m in user_lang_neutral])

            if candidate_messages: # If user messages are found, pick one and return
                logging.info(f"Found user-customized messages (lang: {self.language_code} or neutral). Using one.")
                return random.choice(candidate_messages)

            # 2. If no user messages, proceed with system messages
            system_messages_crud = GenericCRUD(conn, 'motivational_messages', 'id')
            current_day_of_year = datetime.date.today().timetuple().tm_yday

            # Try to fetch a system message for the current language and specific day_of_year
            daily_sys_messages = system_messages_crud.get_by_attributes(
                {"language_code": self.language_code, "is_active": True, "day_of_year": current_day_of_year}
            )
            if daily_sys_messages:
                logging.info(f"Found daily system message for lang '{self.language_code}', day {current_day_of_year}.")
                return random.choice(daily_sys_messages)['message']

            # If no daily system message, try to fetch a generic system message for the current language
            logging.debug(f"No daily system message. Trying generic for lang '{self.language_code}'.")
            generic_sys_lang_messages = system_messages_crud.get_by_attributes(
                {"language_code": self.language_code, "is_active": True, "day_of_year": None}
            )
            if generic_sys_lang_messages:
                logging.info(f"Found generic system message for lang '{self.language_code}'.")
                return random.choice(generic_sys_lang_messages)['message']

            # If still no system message, try to fetch a generic 'en' system message
            if self.language_code != 'en':
                logging.warning(f"No generic system messages for lang '{self.language_code}'. Falling back to 'en' generic system.")
                english_generic_sys_messages = system_messages_crud.get_by_attributes(
                    {"language_code": "en", "is_active": True, "day_of_year": None}
                )
                if english_generic_sys_messages:
                    logging.info("Found generic system message for lang 'en'.")
                    return random.choice(english_generic_sys_messages)['message']

            # Ultimate fallback
            logging.error("No messages found in DB (user, daily system, generic system). Using hardcoded default.")
            return "Welcome! / Bienvenue !" # Corrected Indentation and removed dead code below

        # Dead code, removed: return random.choice(messages)['message']

        except Exception as e:
            logging.error(f"Error fetching motivational message from DB: {e}", exc_info=True)
            # Fallback to a hardcoded message in case of any DB error
            hardcoded_fallback_messages = [
                "Chaque jour est une nouvelle opportunité.", "Croyez en vous et tout deviendra possible.",
                "Every day is a new opportunity.", "Believe in yourself and anything is possible."
            ]
            return random.choice(hardcoded_fallback_messages)
        finally:
            if conn:
                conn.close()

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

    def _start_fade_in(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(700) # milliseconds
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

    def show_splash(self):
        super().show() # Call QWidget's show method
        self._center_on_screen()
        self._start_fade_in() # Start fade-in after showing and centering
        QApplication.instance().processEvents()


    def finish_splash(self, main_window):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(700) # milliseconds
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        # Connect finished signal to actually close/hide the window
        # Important: Use self.close to ensure widget is destroyed and resources are freed.
        # If using self.hide(), the widget remains in memory.
        self.animation.finished.connect(self.close)

        self.animation.start()

        # Stop the GIF movie when starting fade out, not after it's hidden
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
