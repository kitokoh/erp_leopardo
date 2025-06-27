# Widget to display calculation history

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton,
                             QHBoxLayout, QLabel, QDialog, QScrollArea,
                             QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt

class HistoryDisplayWidget(QDialog):
    """
    A QDialog widget to display calculation history for a specific user.
    It retrieves history entries from a HistoryManager and displays them in a
    QTextEdit with HTML formatting. Allows refreshing and clearing the history.
    Styling is intended to be applied via QSS through objectNames.
    """
    def __init__(self, history_manager, user_id, parent=None):
        """
        Initializes the HistoryDisplayWidget.
        Args:
            history_manager: An instance of HistoryManager to fetch/clear history.
            user_id: The ID of the user whose history is to be displayed/managed.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setObjectName("HistoryDisplayDialog") # For QSS
        self.history_manager = history_manager
        self.user_id = user_id
        self.setWindowTitle(f"Historique des Calculs - Utilisateur: {self.user_id}")
        self.setMinimumSize(500, 400)
        self.setModal(False)

        self.layout = QVBoxLayout(self)

        self.history_text_edit = QTextEdit(self)
        self.history_text_edit.setObjectName("historyTextEdit")
        self.history_text_edit.setReadOnly(True)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.history_text_edit)
        self.layout.addWidget(scroll_area)

        buttons_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Rafraîchir")
        self.refresh_button.setObjectName("refreshHistoryButton")
        self.refresh_button.clicked.connect(self.populate_history)
        self.clear_button = QPushButton("Effacer Mon Historique (BDD)")
        self.clear_button.setObjectName("clearHistoryButton")
        self.clear_button.clicked.connect(self.confirm_clear_history)

        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        self.layout.addLayout(buttons_layout)

        self.populate_history()

    def populate_history(self, user_id_to_load=None):
        """
        Populates the history display area with entries for the current or specified user.
        Fetches data from the HistoryManager and formats it as HTML.
        Args:
            user_id_to_load (str, optional): If provided, loads history for this user ID
                                             instead of the one stored in self.user_id.
        """
        current_user_id = user_id_to_load if user_id_to_load else self.user_id
        self.setWindowTitle(f"Historique des Calculs - Utilisateur: {current_user_id}")

        self.history_text_edit.clear()
        if not self.history_manager:
            self.history_text_edit.setHtml("<p style='color: red;'><i>Erreur: HistoryManager non initialisé.</i></p>")
            return
        if not current_user_id:
            self.history_text_edit.setHtml("<p style='color: red;'><i>Erreur: ID Utilisateur non défini pour chargement.</i></p>")
            return

        history_entries = self.history_manager.get_history(user_id=current_user_id)
        if not history_entries:
            self.history_text_edit.setHtml(f"<p style='color: #777;'><i>L'historique est vide pour {current_user_id}.</i></p>")
            return

        html_content = ""
        for entry in history_entries:
            calc_type_display = entry.get('calculator_type', 'N/A')
            expr_display = Qt.escape(str(entry.get('expression', '')))
            res_display = Qt.escape(str(entry.get('result', '')))
            timestamp_display = entry.get('timestamp', 'N/A')

            html_content += (
                f"<div style='margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;'>"
                f"<small style='color: #555;'>{timestamp_display} - Type: <b>{calc_type_display}</b></small><br/>"
                f"<b>Expression:</b> <pre style='display: inline; margin:0; padding:0; white-space: pre-wrap; word-wrap: break-word;'>{expr_display}</pre><br/>"
                f"<b>Résultat:</b> <span style='color: #007700; font-weight: bold;'>{res_display}</span>"
                f"</div>"
            )
        self.history_text_edit.setHtml(html_content)

    def confirm_clear_history(self):
        """
        Asks for user confirmation before clearing the history for the current user
        from the database via HistoryManager. Refreshes the display afterwards.
        """
        if not self.user_id:
            QMessageBox.warning(self, "Erreur", "ID Utilisateur non défini. Impossible d'effacer l'historique.")
            return

        reply = QMessageBox.question(self, "Confirmer Suppression",
                                     f"Êtes-vous sûr de vouloir effacer tout l'historique pour l'utilisateur '{self.user_id}' de la base de données?\n"
                                     "Cette action est irréversible.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.history_manager and hasattr(self.history_manager, 'clear_history'):
                if self.history_manager.clear_history(user_id=self.user_id):
                    QMessageBox.information(self, "Historique Effacé", f"L'historique pour {self.user_id} a été effacé de la base de données.")
                else:
                    QMessageBox.warning(self, "Erreur", f"Impossible d'effacer l'historique pour {self.user_id} de la base de données.")
            else:
                QMessageBox.critical(self, "Erreur Manager", "HistoryManager non disponible ou méthode clear_history manquante.")
            self.populate_history()


    def showEvent(self, event):
        """
        Overrides QDialog.showEvent to refresh history when the dialog is shown.
        """
        self.populate_history()
        super().showEvent(event)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from .history_manager import HistoryManager
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base as CalculatorBase # Ensure correct Base import
    import os

    app = QApplication(sys.argv)

    # --- Attempt to load QSS for standalone testing ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Path relative to this history_display_widget.py file
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss:
            app.setStyleSheet(f.read())
            print(f"INFO (HistoryDisplayWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (HistoryDisplayWidget Test): Could not load QSS from {qss_file_path}. {e}")
    # --- End Load QSS ---

    # Use a file-based DB for this test to check persistence if app is run multiple times
    db_file = "test_history_display_standalone.db"
    engine = create_engine(f'sqlite:///{db_file}')
    CalculatorBase.metadata.create_all(engine) # Create table if it doesn't exist
    TestSessionLocalDialog = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    test_user = "standalone_history_tester"
    test_hm_dialog = HistoryManager(db_session_factory=TestSessionLocalDialog)

    # Add some dummy entries for testing display
    if not test_hm_dialog.get_history(user_id=test_user, limit=1): # Add only if empty for this user
        print(f"Adding initial test entries for user '{test_user}' in {db_file}")
        test_hm_dialog.add_entry("Commercial Test", "22+33", "55", user_id=test_user)
        test_hm_dialog.add_entry("Scientific Test", "sqrt(144)", "12", user_id=test_user)
    else:
        print(f"History for user '{test_user}' already exists in {db_file}.")


    history_dialog = HistoryDisplayWidget(history_manager=test_hm_dialog, user_id=test_user)
    # history_dialog.setObjectName("HistoryDisplayDialog") # Already set in __init__
    history_dialog.show()

    sys.exit(app.exec_())
