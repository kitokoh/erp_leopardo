# Widget and logic for the Press Tonnage Calculator

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFormLayout,
                             QGroupBox, QComboBox)
from PyQt5.QtCore import Qt
import math
from .history_manager import HistoryManager

class TonnageCalculatorWidget(QWidget):
    """
    Calculates the required tonnage for sheet metal bending operations.
    Allows input of material properties, dimensions, and V-die opening.
    """
    def __init__(self, parent=None, history_manager=None):
        """
        Initializes the TonnageCalculatorWidget.
        Args:
            parent: The parent widget.
            history_manager: An instance of HistoryManager for logging.
        """
        super().__init__(parent)
        self.setObjectName("TonnageCalculatorWidget")

        self.history_manager = history_manager if history_manager else HistoryManager()
        # self.parent_main_calc_widget = parent # Use parent() if MainCalculatorWidget.add_to_history is called

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)

        # --- Input Group ---
        input_group = QGroupBox("Paramètres de Pliage")
        input_group.setObjectName("tonnageInputGroup")
        form_layout = QFormLayout(input_group)
        form_layout.setSpacing(8)

        self.bending_length_input = QLineEdit(self)
        self.bending_length_input.setPlaceholderText("mm")
        self.bending_length_input.setToolTip("Longueur de la ligne de pliage (L).")

        self.sheet_thickness_input = QLineEdit(self)
        self.sheet_thickness_input.setPlaceholderText("mm")
        self.sheet_thickness_input.setToolTip("Épaisseur de la tôle (e).")

        self.material_uts_input = QLineEdit(self) # UTS = Ultimate Tensile Strength (Rm)
        self.material_uts_input.setPlaceholderText("MPa (N/mm²)")
        self.material_uts_input.setToolTip("Résistance à la traction du matériau (Rm).\nEx: Acier doux (S235JR) ~ 360-510 MPa, Inox 304 ~ 520 MPa.")

        self.v_die_opening_input = QLineEdit(self)
        self.v_die_opening_input.setPlaceholderText("mm (généralement 6-12 x épaisseur)")
        self.v_die_opening_input.setToolTip("Ouverture du Vé de la matrice (V). Recommandé: 6-8 x e (acier), 8-12 x e (inox/alu).")

        # Material ComboBox (Optional enhancement later)
        # self.material_combo = QComboBox(self)
        # self.material_combo.addItems(["Acier Doux (S235 ~400MPa)", "Acier S355 (~500MPa)", "Inox 304 (~520MPa)", "Aluminium (~100-300MPa)", "Autre (Rm manuel)"])
        # self.material_combo.currentIndexChanged.connect(self.on_material_selected)
        # form_layout.addRow(QLabel("Matériau:"), self.material_combo)

        form_layout.addRow(QLabel("Longueur de Pliage (L):"), self.bending_length_input)
        form_layout.addRow(QLabel("Épaisseur Tôle (e):"), self.sheet_thickness_input)
        form_layout.addRow(QLabel("Résistance Matériau (Rm):"), self.material_uts_input)
        form_layout.addRow(QLabel("Ouverture Vé (V):"), self.v_die_opening_input)

        self.layout.addWidget(input_group)

        self.calculate_tonnage_button = QPushButton("Calculer Tonnage")
        self.calculate_tonnage_button.setObjectName("calculateTonnageButton")
        self.calculate_tonnage_button.clicked.connect(self.perform_tonnage_calculation)
        self.layout.addWidget(self.calculate_tonnage_button, alignment=Qt.AlignCenter)

        # --- Output Group ---
        output_group = QGroupBox("Résultat Tonnage")
        output_group.setObjectName("tonnageOutputGroup")
        results_form_layout = QFormLayout(output_group) # Using QFormLayout for single result too

        self.required_tonnage_label = QLabel("- Tonnes")
        self.required_tonnage_label.setObjectName("tonnageResultLabel")
        self.required_tonnage_label.setStyleSheet("font-weight: bold; font-size: 16pt;") # Temp style

        results_form_layout.addRow(QLabel("Tonnage Requis:"), self.required_tonnage_label)
        self.layout.addWidget(output_group)
        self.layout.addStretch()

    # def on_material_selected(self):
    #     # Placeholder for logic if a material combobox is added
    #     pass

    def get_float_input(self, line_edit: QLineEdit, field_name: str, allow_zero=False) -> float | None:
        """
        Helper function to get and validate a float value from a QLineEdit.
        Displays a QMessageBox on error.

        Args:
            line_edit (QLineEdit): The QLineEdit widget to get text from.
            field_name (str): The user-friendly name of the field for error messages.
            allow_zero (bool): Whether zero is an acceptable value for this field.

        Returns:
            float | None: The float value if valid, otherwise None.
        """
        try:
            val_str = line_edit.text().strip().replace(',', '.')
            if not val_str:
                QMessageBox.warning(self, "Entrée Manquante", f"Le champ '{field_name}' est requis.")
                return None
            val = float(val_str)
            if val < 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{field_name}' ne peut pas être négative.")
                return None
            if not allow_zero and val == 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{field_name}' doit être positive.")
                return None
            return val
        except ValueError:
            QMessageBox.warning(self, "Entrée Invalide", f"Veuillez entrer une valeur numérique valide pour '{field_name}'.")
            return None

    def perform_tonnage_calculation(self):
        """
        Calculates the required tonnage for V-bending based on user inputs.
        Uses a common formula for air bending. Updates the result label and logs
        the calculation to history.
        Formula: Force_kN = (C * L * e^2 * Rm) / (V * 1000)
                 Tonnage = Force_kN / 9.80665
        Where C is a die factor (e.g., 1.33).
        """
        self.required_tonnage_label.setText("- Tonnes")

        length_mm = self.get_float_input(self.bending_length_input, "Longueur de Pliage")
        thickness_mm = self.get_float_input(self.sheet_thickness_input, "Épaisseur Tôle")
        uts_mpa = self.get_float_input(self.material_uts_input, "Résistance Matériau") # Rm in N/mm²
        v_opening_mm = self.get_float_input(self.v_die_opening_input, "Ouverture Vé")

        if None in [length_mm, thickness_mm, uts_mpa, v_opening_mm]:
            return # Error already shown

        # Bending Force Calculation (common formula for V-bending)
        # F_kN = (C * L * S^2 * Rm) / (V * 1000)
        # Where:
        # F_kN = Force in kiloNewtons
        # C = Die opening factor (typically 1.2 to 1.4 for air bending, common default 1.33 or 1.41 for DIN 6935)
        # L = Bending length in mm
        # S = Sheet thickness in mm
        # Rm = Material tensile strength in MPa (N/mm^2)
        # V = V-die opening in mm
        # 1000 = conversion factor for kN

        # Using a common factor for air bending, adjust if needed for specific tooling or standards
        die_factor_C = 1.33

        if v_opening_mm == 0: # Prevent division by zero
            QMessageBox.warning(self, "Erreur de Calcul", "L'ouverture du Vé ne peut pas être zéro.")
            return

        try:
            force_kN = (die_factor_C * length_mm * (thickness_mm**2) * uts_mpa) / (v_opening_mm * 1000)

            # Convert kN to metric tons (1 ton = 1000 kgf; 1 kgf = 9.80665 N; 1 kN = 1000 N)
            # Tonnage = Force_kN / 9.80665
            tonnage = force_kN / 9.80665

            self.required_tonnage_label.setText(f"{tonnage:.2f} Tonnes")

            # History Logging
            inputs_summary = (f"L:{length_mm}mm, e:{thickness_mm}mm, Rm:{uts_mpa}MPa, V_ouverture:{v_opening_mm}mm")
            results_summary = f"Tonnage: {tonnage:.2f} T"

            if hasattr(self.parent(), 'add_to_history') and self.parent() is not None:
                self.parent().add_to_history("Tonnage Pliage", inputs_summary, results_summary)
            elif self.history_manager: # Fallback to local if parent or method not found
                 self.history_manager.add_entry(
                    calculator_type="Tonnage Pliage",
                    expression=inputs_summary,
                    result=results_summary,
                    user_id=self.parent().get_current_user_id() if hasattr(self.parent(), 'get_current_user_id') else "standalone_user"
                )

        except Exception as e:
            self.required_tonnage_label.setText("Erreur")
            QMessageBox.critical(self, "Erreur de Calcul", f"Une erreur est survenue: {e}")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import os

    app = QApplication(sys.argv)
    # --- Attempt to load QSS for standalone testing ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss:
            app.setStyleSheet(f.read())
            print(f"INFO (TonnageCalculatorWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (TonnageCalculatorWidget Test): Could not load QSS. {e}")
    # --- End Load QSS ---

    calc = TonnageCalculatorWidget()
    calc.setWindowTitle("Calculatrice de Tonnage Pliage - Test")
    calc.resize(450, 350)
    calc.show()
    sys.exit(app.exec_())
