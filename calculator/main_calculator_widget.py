# Main widget for the calculator module
# This widget will allow users to select and display different calculators

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QStackedWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

# Import calculator widgets and managers
from .commercial_calculator import CommercialCalculatorWidget
from .scientific_calculator import ScientificCalculatorWidget
from .cylinder_calculator import CylinderCalculatorWidget
from .unit_converter_calculator import UnitConverterCalculatorWidget
from .history_manager import HistoryManager
from .history_display_widget import HistoryDisplayWidget

# Attempt to import database session factory from the main application
# This is a placeholder path; it needs to match your project structure.
try:
    from db.connection import SessionLocal as AppSessionLocal # Example path
except ImportError:
    AppSessionLocal = None
    print("WARNING (MainCalculatorWidget): AppSessionLocal not found. Database history persistence will be disabled.")
    print("Ensure 'from db.connection import SessionLocal as AppSessionLocal' works or provide db_session_factory.")

class MainCalculatorWidget(QWidget):
    def __init__(self, parent=None, app_auth_manager=None, db_session_factory=None):
        super().__init__(parent)
        self.setWindowTitle("Module Calculatrices")
        self.setObjectName("MainCalculatorWidget") # For main QSS styling
        self.setMinimumSize(450, 580) # Adjusted min size slightly

        self.app_auth_manager = app_auth_manager
        active_db_session_factory = db_session_factory if db_session_factory else AppSessionLocal

        if active_db_session_factory is None:
            print("ERROR (MainCalculatorWidget): No database session factory. History non-persistent.")

        self.history_manager = HistoryManager(db_session_factory=active_db_session_factory, max_display_items=200)
        self.history_display_dialog = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        top_bar_layout = QHBoxLayout()
        self.calculator_selector = QComboBox(self)
        self.calculator_selector.setObjectName("calculatorSelectorCombo")
        self.calculator_selector.addItem("Calculatrice Commerciale", "commercial")
        self.calculator_selector.addItem("Calculatrice Scientifique", "scientific")
        self.calculator_selector.addItem("Calculatrice Cylindres Hydrauliques", "cylinder")
        self.calculator_selector.addItem("Convertisseur d'Unités", "unit_converter")
        # self.calculator_selector.setStyleSheet("font-size: 14px; padding: 5px; margin-right: 10px;") # Will be handled by QSS
        self.calculator_selector.currentIndexChanged.connect(self.on_calculator_selected)
        top_bar_layout.addWidget(self.calculator_selector, 1)

        self.show_history_button = QPushButton("Historique")
        self.show_history_button.setObjectName("historyButton")
        # self.show_history_button.setStyleSheet("font-size: 14px; padding: 5px;") # Will be handled by QSS
        self.show_history_button.clicked.connect(self.toggle_history_display)
        top_bar_layout.addWidget(self.show_history_button)
        self.layout.addLayout(top_bar_layout)

        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget)

        # Pass the potentially DB-enabled history_manager to calculators that log
        self.commercial_calc_widget = CommercialCalculatorWidget(parent=self, history_manager=self.history_manager)
        self.commercial_calc_widget.setObjectName("CommercialCalculatorWidget")

        self.scientific_calc_widget = ScientificCalculatorWidget(parent=self, history_manager=self.history_manager)
        self.scientific_calc_widget.setObjectName("ScientificCalculatorWidget")

        self.cylinder_calc_widget = CylinderCalculatorWidget(parent=self, history_manager=self.history_manager)
        self.cylinder_calc_widget.setObjectName("CylinderCalculatorWidget")

        self.unit_converter_widget = UnitConverterCalculatorWidget(parent=self)
        self.unit_converter_widget.setObjectName("UnitConverterCalculatorWidget")

        self.calculators = {
            "commercial": self.commercial_calc_widget,
            "scientific": self.scientific_calc_widget,
            "cylinder": self.cylinder_calc_widget,
            "unit_converter": self.unit_converter_widget,
        }
        for widget_key in self.calculators:
            self.stacked_widget.addWidget(self.calculators[widget_key])

        self.on_calculator_selected(0)

    def on_calculator_selected(self, index):
        selected_data = self.calculator_selector.itemData(index)
        if selected_data in self.calculators:
            self.stacked_widget.setCurrentWidget(self.calculators[selected_data])
        else:
            print(f"Avertissement: Calculatrice pour la clé '{selected_data}' non trouvée.")

    def get_current_user_id(self):
        if self.app_auth_manager and hasattr(self.app_auth_manager, 'get_current_user_id_str'):
            try:
                user_id = self.app_auth_manager.get_current_user_id_str()
                return user_id if user_id else "utilisateur_inconnu"
            except Exception as e:
                print(f"Erreur lors de la récupération de l'ID utilisateur: {e}")
                return "erreur_id_utilisateur"
        return "utilisateur_desktop_simule"

    def add_to_history(self, calc_type, expression, result):
        user_id = self.get_current_user_id()
        # HistoryManager now handles DB interaction if session factory is available
        self.history_manager.add_entry(
            calculator_type=str(calc_type),
            expression=str(expression),
            result=str(result),
            user_id=str(user_id)
        )
        if self.history_display_dialog and self.history_display_dialog.isVisible():
            self.history_display_dialog.populate_history(user_id) # Pass user_id to load specific history

    def toggle_history_display(self):
        current_user_id = self.get_current_user_id()
        if self.history_display_dialog is None:
            self.history_display_dialog = HistoryDisplayWidget(
                history_manager=self.history_manager,
                user_id=current_user_id, # Pass current user_id on creation
                parent=self
            )
        else:
            # Update user_id in case it changed (e.g. user logged out and in)
            self.history_display_dialog.user_id = current_user_id

        if self.history_display_dialog.isVisible():
            self.history_display_dialog.hide()
        else:
            self.history_display_dialog.populate_history() # populate_history will use its stored user_id
            self.history_display_dialog.show()
            self.history_display_dialog.raise_()
            self.history_display_dialog.activateWindow()

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import os # For path joining
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from calculator.models import Base as CalculatorBase

    class MockAuthManager:
        def __init__(self, user_id="test_user_main_calc"):
            self._user_id = user_id
        def get_current_user_id_str(self):
            return self._user_id
        def set_user_id(self, new_id):
            self._user_id = new_id

    engine = create_engine('sqlite:///./test_calculator_history.db')
    CalculatorBase.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = QApplication(sys.argv)

    # --- Load QSS ---
    # Construct the path to the QSS file relative to this script
    # This assumes main_calculator_widget.py is in the 'calculator' directory
    # and the QSS is in 'calculator/styles/calculator_style.qss'
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss:
            app.setStyleSheet(f.read())
            print(f"INFO: Loaded QSS from {qss_file_path}")
    except FileNotFoundError:
        print(f"WARNING: QSS file not found at {qss_file_path}. Using default styles.")
    except Exception as e:
        print(f"ERROR: Could not load QSS file: {e}")
    # --- End Load QSS ---

    mock_auth = MockAuthManager()
    main_calc_app = MainCalculatorWidget(app_auth_manager=mock_auth, db_session_factory=TestSessionLocal)

    main_calc_app.show()
    sys.exit(app.exec_())
