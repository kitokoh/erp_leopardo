# Widget and logic for the Cylinder Calculator

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFormLayout,
                             QGroupBox,QSizePolicy, QComboBox) # Added QComboBox
from PyQt5.QtCore import Qt
import math
from .history_manager import HistoryManager

# Constants for conversions
BAR_TO_N_MM2 = 0.1  # 1 bar = 0.1 N/mm^2 (MPa)
LPM_TO_MM3_S = 1000000 / 60 # L/min to mm^3/s
N_TO_KGF = 1 / 9.80665 # Newton to kg-force

class CylinderCalculatorWidget(QWidget):
    """
    A QWidget for calculating hydraulic cylinder performance characteristics,
    including forces, speeds, volumes, and rod buckling analysis.
    User inputs piston diameter, rod diameter, stroke, pressure, and flow rate.
    Additional inputs are required for buckling calculation (rod length, end conditions, material E, safety factor).
    Results are displayed with multiple common units.
    Styling is intended to be applied via QSS through objectNames.
    """
    def __init__(self, parent=None, history_manager=None):
        """
        Initializes the CylinderCalculatorWidget.
        Args:
            parent: The parent widget, typically MainCalculatorWidget.
            history_manager: An instance of HistoryManager for logging calculations.
        """
        super().__init__(parent)

        self.history_manager = history_manager if history_manager else HistoryManager()
        self.parent_main_calc_widget = parent

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        # Input Group
        input_group = QGroupBox("Paramètres d'entrée du Vérin")
        input_group.setObjectName("inputGroupCylinder")
        # input_group.setStyleSheet("font-weight: bold;") # From QSS
        form_layout = QFormLayout(input_group)
        form_layout.setSpacing(8)

        self.diameter_input = QLineEdit(self)
        self.diameter_input.setPlaceholderText("mm")
        self.diameter_input.setToolTip("Diamètre intérieur du cylindre (D)")
        self.stroke_input = QLineEdit(self)
        self.stroke_input.setPlaceholderText("mm")
        self.stroke_input.setToolTip("Course du piston (S)")
        self.pressure_input = QLineEdit(self)
        self.pressure_input.setPlaceholderText("bar")
        self.pressure_input.setToolTip("Pression hydraulique appliquée (P)")
        self.rod_diameter_input = QLineEdit(self)
        self.rod_diameter_input.setPlaceholderText("mm (0 si simple effet)")
        self.rod_diameter_input.setToolTip("Diamètre de la tige du piston (d). Mettre 0 si vérin simple effet ou si la force de rappel n'est pas hydraulique.")
        self.flow_rate_input = QLineEdit(self)
        self.flow_rate_input.setPlaceholderText("L/min (optionnel)")
        self.flow_rate_input.setToolTip("Débit d'huile alimentant le vérin (Q), pour calcul de vitesse.")

        form_layout.addRow(QLabel("Diamètre Piston (D):"), self.diameter_input)
        form_layout.addRow(QLabel("Course (S):"), self.stroke_input)
        form_layout.addRow(QLabel("Pression (P):"), self.pressure_input)
        form_layout.addRow(QLabel("Diamètre Tige (d):"), self.rod_diameter_input)
        form_layout.addRow(QLabel("Débit (Q):"), self.flow_rate_input)
        self.layout.addWidget(input_group)

        self.calculate_button = QPushButton("Calculer les Performances")
        self.calculate_button.setObjectName("calculateCylinderButton")
        # self.calculate_button.setStyleSheet(...) # From QSS
        self.calculate_button.clicked.connect(self.perform_calculations)
        self.layout.addWidget(self.calculate_button, alignment=Qt.AlignCenter)

        # Output Group
        output_group = QGroupBox("Résultats de Performance du Vérin")
        output_group.setObjectName("resultsGroupCylinder")
        # output_group.setStyleSheet("font-weight: bold;") # From QSS
        self.results_layout = QGridLayout(output_group)
        self.results_layout.setSpacing(8)

        self.result_labels = {}
        result_keys = [
            "piston_area", "annular_area", "force_push", "force_pull",
            "volume_push", "volume_pull", "speed_push", "speed_pull",
            "time_push", "time_pull", "ratio"
        ]
        for key in result_keys:
            self.result_labels[key] = QLabel("-")
            self.result_labels[key].setObjectName("cylinderResultLabel") # Apply to all result labels
            # self.result_labels[key].setStyleSheet(...) # From QSS
            self.result_labels[key].setMinimumWidth(200)
            self.result_labels[key].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ... (Populating results_layout as before) ...
        self.results_layout.addWidget(QLabel("Surface Piston (Aₚ):"), 0, 0)
        self.results_layout.addWidget(self.result_labels["piston_area"], 0, 1)
        self.results_layout.addWidget(QLabel("Surface Annulaire (Aₐ):"), 1, 0)
        self.results_layout.addWidget(self.result_labels["annular_area"], 1, 1)
        self.results_layout.addWidget(QLabel("Force Poussée (Fₚ):"), 2, 0)
        self.results_layout.addWidget(self.result_labels["force_push"], 2, 1)
        self.results_layout.addWidget(QLabel("Force Traction (Fₜ):"), 3, 0)
        self.results_layout.addWidget(self.result_labels["force_pull"], 3, 1)
        self.results_layout.addWidget(QLabel("Volume Piston (Vₚ):"), 4, 0)
        self.results_layout.addWidget(self.result_labels["volume_push"], 4, 1)
        self.results_layout.addWidget(QLabel("Volume Annulaire (Vₐ):"), 5, 0)
        self.results_layout.addWidget(self.result_labels["volume_pull"], 5, 1)
        self.results_layout.addWidget(QLabel("Vitesse Poussée (vₚ):"), 0, 2)
        self.results_layout.addWidget(self.result_labels["speed_push"], 0, 3)
        self.results_layout.addWidget(QLabel("Vitesse Traction (vₜ):"), 1, 2)
        self.results_layout.addWidget(self.result_labels["speed_pull"], 1, 3)
        self.results_layout.addWidget(QLabel("Temps Poussée (tₚ):"), 2, 2)
        self.results_layout.addWidget(self.result_labels["time_push"], 2, 3)
        self.results_layout.addWidget(QLabel("Temps Traction (tₜ):"), 3, 2)
        self.results_layout.addWidget(self.result_labels["time_pull"], 3, 3)
        self.results_layout.addWidget(QLabel("Ratio (φ = Aₚ/Aₐ):"), 4, 2)
        self.results_layout.addWidget(self.result_labels["ratio"], 4, 3)
        self.results_layout.setColumnStretch(1, 1)
        self.results_layout.setColumnStretch(3, 1)
        self.layout.addWidget(output_group)

        # --- Buckling Calculation Group ---
        buckling_group = QGroupBox("Calcul de Flambage de la Tige")
        buckling_group.setObjectName("bucklingGroupCylinder")
        # buckling_group.setStyleSheet("font-weight: bold;") # From QSS
        buckling_form_layout = QFormLayout(buckling_group)
        buckling_form_layout.setSpacing(8)

        self.longueur_libre_tige_input = QLineEdit(self)
        self.longueur_libre_tige_input.setPlaceholderText("mm")
        self.longueur_libre_tige_input.setToolTip("Longueur de la tige non supportée, entre appuis (L).")

        self.coeff_extremite_input = QComboBox(self)
        self.coeff_extremite_input.setToolTip("Coefficient K pour la longueur effective (L_eff = K * L), basé sur les conditions de fixation.")
        self.coeff_extremite_input.addItem("Articulé - Articulé (K=1.0)", 1.0)
        self.coeff_extremite_input.addItem("Encastré - Encastré (K=0.5)", 0.5)
        self.coeff_extremite_input.addItem("Encastré - Articulé (K=0.7)", 0.7) # Common approximation
        self.coeff_extremite_input.addItem("Encastré - Libre (K=2.0)", 2.0)

        self.module_young_input = QLineEdit(self)
        self.module_young_input.setPlaceholderText("GPa (ex: 210 pour acier)")
        self.module_young_input.setText("210")
        self.module_young_input.setToolTip("Module d'Young du matériau de la tige (E). Acier ~200-210 GPa.")

        self.safety_factor_buckling_input = QLineEdit(self)
        self.safety_factor_buckling_input.setPlaceholderText("ex: 2.5 à 3.5")
        self.safety_factor_buckling_input.setText("3.0")
        self.safety_factor_buckling_input.setToolTip("Facteur de sécurité souhaité pour le flambage.")

        buckling_form_layout.addRow(QLabel("Longueur Libre Tige (L):"), self.longueur_libre_tige_input)
        buckling_form_layout.addRow(QLabel("Coeff. Fixation (K):"), self.coeff_extremite_input)
        buckling_form_layout.addRow(QLabel("Module d'Young (E):"), self.module_young_input)
        buckling_form_layout.addRow(QLabel("Facteur Sécurité (FS):"), self.safety_factor_buckling_input)

        self.result_labels["force_critique_flambage"] = QLabel("-")
        self.result_labels["force_critique_flambage"].setObjectName("cylinderResultLabel") # Consistent styling
        # self.result_labels["force_critique_flambage"].setStyleSheet(...) # From QSS
        self.result_labels["charge_adm_flambage"] = QLabel("-")
        self.result_labels["charge_adm_flambage"].setObjectName("cylinderResultLabel") # Consistent styling
        # self.result_labels["charge_adm_flambage"].setStyleSheet(...) # From QSS
        self.buckling_warning_label = QLabel("")
        self.buckling_warning_label.setObjectName("bucklingWarningLabel") # Already has specific QSS
        self.buckling_warning_label.setVisible(False)
        self.buckling_warning_label.setWordWrap(True)


        buckling_form_layout.addRow(QLabel("Force Critique Flambage (F_crit):"), self.result_labels["force_critique_flambage"])
        buckling_form_layout.addRow(QLabel("Charge Adm. Flambage (F_adm):"), self.result_labels["charge_adm_flambage"])
        buckling_form_layout.addRow(self.buckling_warning_label)

        self.layout.addWidget(buckling_group)
        self.layout.addStretch()

        self.setStyleSheet("""
            QWidget { background-color: #fafafa; font-size: 14px; }
            QGroupBox { margin-top: 1ex; border: 1px solid #cfd8dc; border-radius: 5px; padding: 8px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; margin-left: 5px;}
            QLabel { padding: 3px; font-weight: normal; }
            QLineEdit { padding: 6px; border: 1px solid #b0bec5; border-radius: 3px; background-color: white; }
            QPushButton { border-radius: 4px; }
            #buckling_warning_label { color: red; font-weight: bold; }
        """) # This will be removed, but keep the buckling_warning_label ID for QSS file.
            # The main widget (CylinderCalculatorWidget) itself will get its style from QSS via its objectName.

        self.last_calculated_push_force_N = 0.0

        # Connect signals for dynamic recalculation or clearing of buckling results
        self.calculate_button.clicked.connect(self.perform_buckling_calculation_if_possible) # Re-calc buckling after main calc
        for line_edit in [self.longueur_libre_tige_input, self.module_young_input, self.safety_factor_buckling_input, self.rod_diameter_input]:
            line_edit.textChanged.connect(self.perform_buckling_calculation_if_possible)
        self.coeff_extremite_input.currentIndexChanged.connect(self.perform_buckling_calculation_if_possible)
        self.rod_diameter_input.textChanged.connect(self.clear_buckling_results_on_rod_dia_change)


    def clear_buckling_results_on_rod_dia_change(self):
        if "force_critique_flambage" in self.result_labels:
            self.result_labels["force_critique_flambage"].setText("-")
            self.result_labels["charge_adm_flambage"].setText("-")
            self.buckling_warning_label.setText("")
            self.buckling_warning_label.setVisible(False)
        self.perform_buckling_calculation_if_possible() # Attempt re-calculation

    def get_float_value(self, line_edit, allow_zero=False, field_name="ce champ"):
        try:
            val_str = line_edit.text().strip().replace(',', '.')
            if not val_str:
                # For optional fields, or fields where 0 is a valid "not provided" or "use default"
                if line_edit in [self.rod_diameter_input,
                                 self.flow_rate_input,
                                 self.longueur_libre_tige_input,
                                 self.module_young_input,
                                 self.safety_factor_buckling_input]:
                    return 0.0 if allow_zero else None # Return 0.0 if zero is explicitly allowed for this optional field
                return None # Required field is empty

            val = float(val_str)
            if val < 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{field_name}' ne peut pas être négative.")
                return None
            if not allow_zero and val == 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{field_name}' doit être positive (non nulle).")
                return None
            return val
        except ValueError:
            QMessageBox.warning(self, "Entrée Invalide", f"Veuillez entrer une valeur numérique valide pour '{field_name}'.")
            return None

    def perform_calculations(self):
        # Reset previous results including buckling
        for key in self.result_labels: self.result_labels[key].setText("-")
        if hasattr(self, 'buckling_warning_label'):
            self.buckling_warning_label.setText("")
            self.buckling_warning_label.setVisible(False)
        self.last_calculated_push_force_N = 0.0

        dia_piston_mm = self.get_float_value(self.diameter_input, field_name=self.diameter_input.toolTip())
        stroke_mm = self.get_float_value(self.stroke_input, field_name=self.stroke_input.toolTip())
        pressure_bar = self.get_float_value(self.pressure_input, field_name=self.pressure_input.toolTip())
        dia_rod_mm = self.get_float_value(self.rod_diameter_input, allow_zero=True, field_name=self.rod_diameter_input.toolTip())
        flow_lpm = self.get_float_value(self.flow_rate_input, allow_zero=True, field_name=self.flow_rate_input.toolTip())

        required_inputs = { self.diameter_input.toolTip(): dia_piston_mm, self.stroke_input.toolTip(): stroke_mm, self.pressure_input.toolTip(): pressure_bar }
        valid_inputs = True
        for name, val in required_inputs.items():
            if val is None or val <= 0:
                if val is None: QMessageBox.warning(self, "Entrée Manquante", f"Le champ '{name}' est requis.")
                else: QMessageBox.warning(self, "Entrée Invalide", f"{name} doit être une valeur positive.")
                valid_inputs = False
                break
        if not valid_inputs: return
        if dia_rod_mm is None: dia_rod_mm = 0.0
        if flow_lpm is None: flow_lpm = 0.0
        if dia_rod_mm >= dia_piston_mm and dia_piston_mm > 0 :
            QMessageBox.warning(self, "Entrée Invalide", "Le diamètre de la tige doit être inférieur au diamètre du piston.")
            return

        area_piston_mm2 = math.pi * (dia_piston_mm / 2)**2
        self.result_labels["piston_area"].setText(f"{area_piston_mm2:.2f} mm² ({area_piston_mm2/100:.2f} cm²)")
        area_rod_mm2 = math.pi * (dia_rod_mm / 2)**2 if dia_rod_mm > 0 else 0
        area_annular_mm2 = area_piston_mm2 - area_rod_mm2
        self.result_labels["annular_area"].setText(f"{area_annular_mm2:.2f} mm² ({area_annular_mm2/100:.2f} cm²)" if dia_rod_mm > 0 else "N/A (simple effet)")
        pressure_N_mm2 = pressure_bar * BAR_TO_N_MM2
        force_push_N = area_piston_mm2 * pressure_N_mm2
        self.result_labels["force_push"].setText(f"{force_push_N:.2f} N ({force_push_N * N_TO_KGF:.2f} kgf) ({force_push_N/1000:.2f} kN)")
        self.last_calculated_push_force_N = force_push_N

        force_pull_N_val = area_annular_mm2 * pressure_N_mm2 if dia_rod_mm > 0 else 0
        self.result_labels["force_pull"].setText(f"{force_pull_N_val:.2f} N ({force_pull_N_val * N_TO_KGF:.2f} kgf) ({force_pull_N_val/1000:.2f} kN)" if dia_rod_mm > 0 else "N/A (simple effet)")
        vol_push_mm3 = area_piston_mm2 * stroke_mm
        self.result_labels["volume_push"].setText(f"{vol_push_mm3 / 1000:.2f} cm³ ({vol_push_mm3 / 1000000:.3f} L)")
        vol_pull_mm3 = area_annular_mm2 * stroke_mm if dia_rod_mm > 0 else 0
        self.result_labels["volume_pull"].setText(f"{vol_pull_mm3 / 1000:.2f} cm³ ({vol_pull_mm3 / 1000000:.3f} L)" if dia_rod_mm > 0 else "N/A (simple effet)")
        self.result_labels["ratio"].setText(f"{(area_piston_mm2 / area_annular_mm2):.2f}" if dia_rod_mm > 0 and area_annular_mm2 > 0 else "N/A")

        if flow_lpm > 0:
            flow_mm3_s = flow_lpm * LPM_TO_MM3_S
            if area_piston_mm2 > 0:
                speed_push_mm_s = flow_mm3_s / area_piston_mm2
                self.result_labels["speed_push"].setText(f"{speed_push_mm_s:.2f} mm/s ({speed_push_mm_s / 1000:.3f} m/s)")
                time_push_s = stroke_mm / speed_push_mm_s if speed_push_mm_s > 0 else float('inf')
                self.result_labels["time_push"].setText(f"{time_push_s:.2f} s" if time_push_s != float('inf') else "N/A")
            else:
                self.result_labels["speed_push"].setText("N/A"); self.result_labels["time_push"].setText("N/A")
            if dia_rod_mm > 0 and area_annular_mm2 > 0:
                speed_pull_mm_s = flow_mm3_s / area_annular_mm2
                self.result_labels["speed_pull"].setText(f"{speed_pull_mm_s:.2f} mm/s ({speed_pull_mm_s / 1000:.3f} m/s)")
                time_pull_s = stroke_mm / speed_pull_mm_s if speed_pull_mm_s > 0 else float('inf')
                self.result_labels["time_pull"].setText(f"{time_pull_s:.2f} s" if time_pull_s != float('inf') else "N/A")
            else:
                self.result_labels["speed_pull"].setText("N/A"); self.result_labels["time_pull"].setText("N/A")
        else:
            for key in ["speed_push", "speed_pull", "time_push", "time_pull"]: self.result_labels[key].setText("Débit non fourni")

        inputs_summary = f"D:{dia_piston_mm}mm,S:{stroke_mm}mm,P:{pressure_bar}bar,d:{dia_rod_mm}mm,Q:{flow_lpm}L/min"
        results_summary = f"Fp:{self.last_calculated_push_force_N:.0f}N;Ap:{area_piston_mm2:.0f}mm²"
        if hasattr(self.parent_main_calc_widget, 'add_to_history') and self.parent_main_calc_widget:
            self.parent_main_calc_widget.add_to_history("Vérin Perf.", inputs_summary, results_summary)
        elif self.history_manager: self.history_manager.add_entry("Vérin Perf.", inputs_summary, results_summary)
        self.perform_buckling_calculation_if_possible()

    def perform_buckling_calculation_if_possible(self):
        """
        Calculates the critical buckling force and allowable load for the cylinder rod.
        This method is called automatically when relevant parameters change or after
        the main cylinder performance calculations are done.
        It updates the UI with buckling results and warnings if applicable.
        """
        if "force_critique_flambage" not in self.result_labels: return # Should not happen
        self.result_labels["force_critique_flambage"].setText("-")
        self.result_labels["charge_adm_flambage"].setText("-")
        self.buckling_warning_label.setText(""); self.buckling_warning_label.setVisible(False)

        longueur_libre_mm = self.get_float_value(self.longueur_libre_tige_input, allow_zero=True, field_name=self.longueur_libre_tige_input.toolTip())
        module_young_gpa = self.get_float_value(self.module_young_input, allow_zero=True, field_name=self.module_young_input.toolTip())
        safety_factor = self.get_float_value(self.safety_factor_buckling_input, allow_zero=True, field_name=self.safety_factor_buckling_input.toolTip())
        dia_rod_mm_buckling = self.get_float_value(self.rod_diameter_input, allow_zero=True, field_name=self.rod_diameter_input.toolTip())

        if not all(x is not None for x in [longueur_libre_mm, module_young_gpa, safety_factor, dia_rod_mm_buckling]): return
        if dia_rod_mm_buckling <= 0: self.result_labels["force_critique_flambage"].setText("Ø tige > 0 requis"); return
        if longueur_libre_mm <= 0: self.result_labels["force_critique_flambage"].setText("L > 0 requis"); return
        if module_young_gpa <= 0: self.result_labels["force_critique_flambage"].setText("E > 0 requis"); return
        if safety_factor <= 0: self.result_labels["force_critique_flambage"].setText("FS > 0 requis"); return

        k_factor = self.coeff_extremite_input.currentData()
        if k_factor is None: QMessageBox.warning(self, "Erreur", "Coeff. d'extrémité non sélectionné."); return

        E_N_mm2 = module_young_gpa * 1000
        I_mm4 = (math.pi * (dia_rod_mm_buckling**4)) / 64
        effective_length_mm = k_factor * longueur_libre_mm
        if effective_length_mm == 0: self.result_labels["force_critique_flambage"].setText("L_eff > 0 requis"); return

        F_crit_N = ((math.pi**2) * E_N_mm2 * I_mm4) / (effective_length_mm**2)
        self.result_labels["force_critique_flambage"].setText(f"{F_crit_N:.2f} N ({F_crit_N/1000:.2f} kN)")
        F_adm_N = F_crit_N / safety_factor
        self.result_labels["charge_adm_flambage"].setText(f"{F_adm_N:.2f} N ({F_adm_N/1000:.2f} kN)")

        if self.last_calculated_push_force_N > 0:
            if F_adm_N < self.last_calculated_push_force_N:
                self.buckling_warning_label.setText(f"ATTENTION: Risque de flambage! (F_poussée {self.last_calculated_push_force_N:.0f}N > F_adm {F_adm_N:.0f}N)")
                self.buckling_warning_label.setVisible(True)
            elif F_adm_N < self.last_calculated_push_force_N * 1.2:
                 self.buckling_warning_label.setText(f"AVERTISSEMENT: F_adm flambage ({F_adm_N:.0f}N) proche de F_poussée ({self.last_calculated_push_force_N:.0f}N).")
                 self.buckling_warning_label.setVisible(True)

        inputs_buckling_summary = f"L:{longueur_libre_mm}mm,K:{k_factor},E:{module_young_gpa}GPa,FS:{safety_factor},d_rod:{dia_rod_mm_buckling}mm"
        results_buckling_summary = f"F_crit:{F_crit_N:.0f}N;F_adm:{F_adm_N:.0f}N"
        if hasattr(self.parent_main_calc_widget, 'add_to_history') and self.parent_main_calc_widget:
            self.parent_main_calc_widget.add_to_history("Vérin Flambage", inputs_buckling_summary, results_buckling_summary)
        elif self.history_manager: self.history_manager.add_entry("Vérin Flambage", inputs_buckling_summary, results_buckling_summary)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QScrollArea, QWidget as QBaseWidget
    import sys
    import os

    app = QApplication(sys.argv)

    # --- Attempt to load QSS for standalone testing ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss:
            app.setStyleSheet(f.read())
            print(f"INFO (CylinderCalculatorWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (CylinderCalculatorWidget Test): Could not load QSS. {e}")
    # --- End Load QSS ---

    # Mock parent for history logging
    class MockMainApp(QBaseWidget):
        def __init__(self):
            super().__init__()
            # Simulate a HistoryManager if needed for deeper testing, or pass None
            self.history_manager_instance = HistoryManager(db_session_factory=None) # Non-persistent for this test
        def add_to_history(self, calc_type, expression, result):
            print(f"MockMainApp History: Type='{calc_type}', Expr='{expression}', Res='{result}'")
            # self.history_manager_instance.add_entry(calc_type, expression, result, "test_cyl_user")


    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Use a container widget for the calculator if it's to be scrolled
    calc_widget_container = QBaseWidget()
    main_container_layout = QVBoxLayout(calc_widget_container)

    mock_parent = MockMainApp() # Instantiate mock parent
    # Pass the mock_parent so CylinderCalculatorWidget can call parent().add_to_history
    # Pass its history_manager if you want CylinderCalculatorWidget to use it directly (though it uses parent call)
    calc = CylinderCalculatorWidget(parent=mock_parent, history_manager=mock_parent.history_manager_instance)
    calc.setObjectName("CylinderCalculatorWidget") # Ensure QSS applies if specific styles target this

    main_container_layout.addWidget(calc)
    calc_widget_container.setLayout(main_container_layout) # Set layout for the container

    scroll_area.setWidget(calc_widget_container)
    scroll_area.setWindowTitle("Calculatrice de Vérins Hydrauliques - Test")
    scroll_area.setMinimumSize(700, 750) # Increased height for buckling section
    scroll_area.show()

    sys.exit(app.exec_())
