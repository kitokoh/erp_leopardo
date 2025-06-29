# Widget and logic for the Sheet Metal Bending Calculator

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFormLayout,
                             QGroupBox)
from PyQt5.QtCore import Qt
import math
from .history_manager import HistoryManager

class BendingCalculatorWidget(QWidget):
    """
    Calculates basic sheet metal bending parameters like Bend Allowance,
    Bend Deduction, and developed length for a simple bend.
    """
    def __init__(self, parent=None, history_manager=None):
        """
        Initializes the BendingCalculatorWidget.
        Args:
            parent: The parent widget.
            history_manager: An instance of HistoryManager for logging.
        """
        super().__init__(parent)
        self.setObjectName("BendingCalculatorWidget")

        self.history_manager = history_manager if history_manager else HistoryManager()

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)

        # --- Input Group ---
        input_group = QGroupBox("Paramètres de Cintrage")
        input_group.setObjectName("bendingInputGroup")
        form_layout = QFormLayout(input_group)
        form_layout.setSpacing(8)

        self.thickness_input = QLineEdit(self)
        self.thickness_input.setPlaceholderText("mm")
        self.thickness_input.setToolTip("Épaisseur du matériau (e).")

        self.inner_radius_input = QLineEdit(self)
        self.inner_radius_input.setPlaceholderText("mm")
        self.inner_radius_input.setToolTip("Rayon de cintrage intérieur souhaité (Ri).")

        self.bend_angle_input = QLineEdit(self)
        self.bend_angle_input.setPlaceholderText("degrés")
        self.bend_angle_input.setToolTip("Angle de cintrage (α) - l'angle extérieur formé par le pli (ex: 90° pour un angle droit).")

        self.k_factor_input = QLineEdit(self)
        self.k_factor_input.setPlaceholderText("ex: 0.33 - 0.50")
        self.k_factor_input.setToolTip("Facteur K: position de la fibre neutre (t/e).\nTypique: Acier 0.4-0.5, Alu 0.35-0.45.")
        self.k_factor_input.setText("0.44") # Common default

        # Inputs for simple developed length calculation
        self.leg1_length_input = QLineEdit(self); self.leg1_length_input.setPlaceholderText("mm (optionnel)"); self.leg1_length_input.setToolTip("Longueur de la première jambe droite (L1), mesurée avant le début du rayon.")
        self.leg2_length_input = QLineEdit(self); self.leg2_length_input.setPlaceholderText("mm (optionnel)"); self.leg2_length_input.setToolTip("Longueur de la deuxième jambe droite (L2), mesurée avant le début du rayon.")


        form_layout.addRow(QLabel("Épaisseur (e):"), self.thickness_input)
        form_layout.addRow(QLabel("Rayon Intérieur (Ri):"), self.inner_radius_input)
        form_layout.addRow(QLabel("Angle de Pli (α):"), self.bend_angle_input)
        form_layout.addRow(QLabel("Facteur K:"), self.k_factor_input)
        form_layout.addRow(QLabel("Longueur Jambe 1 (L1):"), self.leg1_length_input)
        form_layout.addRow(QLabel("Longueur Jambe 2 (L2):"), self.leg2_length_input)

        self.layout.addWidget(input_group)

        self.calculate_bending_button = QPushButton("Calculer Paramètres de Cintrage")
        self.calculate_bending_button.setObjectName("calculateBendingButton")
        self.calculate_bending_button.clicked.connect(self.perform_bending_calculation)
        self.layout.addWidget(self.calculate_bending_button, alignment=Qt.AlignCenter)

        # --- Output Group ---
        output_group = QGroupBox("Résultats de Cintrage")
        output_group.setObjectName("bendingOutputGroup")
        results_form_layout = QFormLayout(output_group)

        self.bend_allowance_label = QLabel("- mm")
        self.bend_allowance_label.setObjectName("bendingResultLabel")
        self.bend_deduction_label = QLabel("- mm")
        self.bend_deduction_label.setObjectName("bendingResultLabel")
        self.developed_length_label = QLabel("- mm") # For L1+L2+BA example
        self.developed_length_label.setObjectName("bendingResultLabel")

        results_form_layout.addRow(QLabel("Abattement au Pli (BA):"), self.bend_allowance_label)
        results_form_layout.addRow(QLabel("Déduction de Pli (BD):"), self.bend_deduction_label)
        results_form_layout.addRow(QLabel("Lg Développée (L1+L2+BA):"), self.developed_length_label)
        self.layout.addWidget(output_group)
        self.layout.addStretch()

    def get_float_input(self, line_edit: QLineEdit, field_name: str, allow_zero=False, optional=False) -> float | None:
        """
        Helper function to get and validate a float value from a QLineEdit.
        Displays a QMessageBox on error.

        Args:
            line_edit (QLineEdit): The QLineEdit widget to get text from.
            field_name (str): The user-friendly name of the field for error messages.
            allow_zero (bool): Whether zero is an acceptable value for this field.
            optional (bool): If True, an empty field will be treated as 0.0 instead of an error.

        Returns:
            float | None: The float value if valid, otherwise None.
        """
        try:
            val_str = line_edit.text().strip().replace(',', '.')
            if not val_str:
                if optional: return 0.0 # Return 0.0 for optional fields if empty
                QMessageBox.warning(self, "Entrée Manquante", f"Le champ '{field_name}' est requis.")
                return None
            val = float(val_str)
            if val < 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{field_name}' ne peut pas être négative.")
                return None
            if not allow_zero and val == 0:
                # Allow k-factor to be potentially zero if user really wants, though unusual
                if field_name == "Facteur K" and allow_zero: # Specific check if k-factor could be zero
                     pass
                else:
                    QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{field_name}' doit être positive.")
                    return None
            return val
        except ValueError:
            QMessageBox.warning(self, "Entrée Invalide", f"Veuillez entrer une valeur numérique valide pour '{field_name}'.")
            return None

    def perform_bending_calculation(self):
        """
        Calculates Bend Allowance (BA), Bend Deduction (BD), and an example
        Developed Length (Ld = L1 + L2 + BA) based on user inputs.
        Updates the result labels and logs the calculation to history.
        """
        self.bend_allowance_label.setText("- mm")
        self.bend_deduction_label.setText("- mm")
        self.developed_length_label.setText("- mm")

        thickness = self.get_float_input(self.thickness_input, "Épaisseur (e)")
        inner_radius = self.get_float_input(self.inner_radius_input, "Rayon Intérieur (Ri)", allow_zero=True) # Ri can be 0
        bend_angle_deg = self.get_float_input(self.bend_angle_input, "Angle de Pli (α)")
        k_factor = self.get_float_input(self.k_factor_input, "Facteur K", allow_zero=True) # K can be small

        leg1 = self.get_float_input(self.leg1_length_input, "Longueur Jambe 1 (L1)", allow_zero=True, optional=True)
        leg2 = self.get_float_input(self.leg2_length_input, "Longueur Jambe 2 (L2)", allow_zero=True, optional=True)


        if None in [thickness, inner_radius, bend_angle_deg, k_factor, leg1, leg2]:
            return # Error already shown by get_float_input

        if not (0 < k_factor <= 1): # K-factor typically between 0 and 1, often ~0.33-0.5
            # Allow slightly outside this for edge cases but warn if totally out
            if not (0 <= k_factor <=1.5): # Wider tolerance before hard error
                QMessageBox.warning(self, "Valeur K-Factor", "Le Facteur K est typiquement entre 0.33 et 0.5. Vérifiez votre valeur.")
                # return # Could choose to stop or allow calculation with unusual K

        if bend_angle_deg <=0 or bend_angle_deg >= 180:
            QMessageBox.warning(self, "Angle Incorrect", "L'angle de pli doit être entre 0 et 180 degrés.")
            return

        bend_angle_rad = math.radians(bend_angle_deg)

        # Bend Allowance (BA) = Angle_rad * (Ri + K * t)
        # This is the length of the arc along the neutral axis.
        bend_allowance = bend_angle_rad * (inner_radius + (k_factor * thickness))
        self.bend_allowance_label.setText(f"{bend_allowance:.3f} mm")

        # Bend Deduction (BD) = 2 * OSL - BA
        # where OSL (Outer Setback) = (Ri + t) * tan(Angle_deg / 2)
        # This is for a 90 degree bend, more generally:
        # BD = 2 * (Ri + t) * tan(alpha_deg / 2) - BA for the included angle.
        # Or, if alpha is the external angle (as defined in tooltip):
        # The "legs" L1 and L2 are measured to the apex of the bend.
        # The total length of the two legs if there were no bend radius (sharp corner) is L1_apex + L2_apex.
        # The developed length is L1_apex + L2_apex - BD.
        # Or, if L1 and L2 are flat lengths before radius starts: Developed Length = L1 + L2 + BA

        # Using a common formula for Bend Deduction:
        # BD = 2 * (tan(Angle_rad / 2)) * (Ri + thickness) - BA
        # This formula for BD assumes the angle is the *included* angle of the bend.
        # If our angle 'alpha' is the *formed* external angle (e.g. 90 for a right angle),
        # then the angle used in tan should be alpha_deg / 2.

        # Let's use the definition that the angle 'alpha' is the *change* in direction.
        # For a 90-degree bend, alpha = 90.
        # OSL (Outer SetBack) = (Ri + t) / tan( (180 - alpha_deg) / 2 )  OR (Ri+t) * tan(alpha_deg/2) if alpha is defined as exterior angle
        # If alpha_deg is the final angle between flanges (e.g. 90 for L-shape), then use (180-alpha_deg) as bend angle for some formulas.
        # Let's assume alpha_deg is the angle of the bend itself (e.g. 90 degrees of bending)

        # A common formula for BD when angle is the *formed* angle (e.g. 90 deg for right angle):
        # BD = 2 * (Ri + thickness) * math.tan(math.radians(bend_angle_deg / 2.0)) - bend_allowance
        # This is often used for external angle.
        # However, if angle is the *bend angle* (how much it's bent from flat), then:
        # OSL = (Ri + thickness) * tan(bend_angle_rad / 2)
        # Bend Deduction BD = 2 * OSL - BA

        # Let's clarify: if user enters 90, it means the part is bent to 90 degrees.
        # The actual arc of bending is over these 90 degrees.
        # OSL = (Ri + t) * tan(bend_angle_rad / 2)
        outer_set_back = (inner_radius + thickness) * math.tan(bend_angle_rad / 2.0)
        bend_deduction = (2 * outer_set_back) - bend_allowance
        self.bend_deduction_label.setText(f"{bend_deduction:.3f} mm")

        # Developed Length (Ld) = L1 + L2 + BA (where L1, L2 are flat lengths next to bend)
        if leg1 > 0 or leg2 > 0 : # Only calculate if at least one leg is given
            developed_length = leg1 + leg2 + bend_allowance
            self.developed_length_label.setText(f"{developed_length:.3f} mm (pour L1+L2+BA)")
        else:
            self.developed_length_label.setText("Entrez L1/L2 pour Ld")


        # History Logging
        inputs_summary = (f"e:{thickness}mm, Ri:{inner_radius}mm, Angle:{bend_angle_deg}°, K:{k_factor}, "
                          f"L1:{leg1 if leg1 else 'N/A'}mm, L2:{leg2 if leg2 else 'N/A'}mm")
        results_summary = f"BA:{bend_allowance:.3f}mm, BD:{bend_deduction:.3f}mm"
        if leg1 > 0 or leg2 > 0:
            results_summary += f", Ld(L1+L2+BA):{developed_length:.3f}mm"

        if hasattr(self.parent(), 'add_to_history') and self.parent() is not None:
            self.parent().add_to_history("Cintrage", inputs_summary, results_summary)
        elif self.history_manager:
             user_id = "standalone_user"
             if hasattr(self.parent(), 'get_current_user_id'):
                 user_id = self.parent().get_current_user_id()
             self.history_manager.add_entry(
                calculator_type="Cintrage",
                expression=inputs_summary,
                result=results_summary,
                user_id=user_id
            )

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
            print(f"INFO (BendingCalculatorWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (BendingCalculatorWidget Test): Could not load QSS. {e}")
    # --- End Load QSS ---

    calc = BendingCalculatorWidget()
    calc.setWindowTitle("Calculatrice de Cintrage - Test")
    calc.resize(480, 450)
    calc.show()
    sys.exit(app.exec_())
