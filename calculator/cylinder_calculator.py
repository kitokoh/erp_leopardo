# Widget and logic for the Cylinder Calculator

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFormLayout,
                             QGroupBox,QSizePolicy, QComboBox)

from PyQt5.QtCore import Qt
import math
from .history_manager import HistoryManager

# Constants for conversions
BAR_TO_N_MM2 = 0.1
N_MM2_TO_BAR = 1 / BAR_TO_N_MM2
LPM_TO_MM3_S = 1000000 / 60
N_TO_KGF = 1 / 9.80665


class CylinderCalculatorWidget(QWidget):
    """
    A QWidget for calculating hydraulic cylinder performance characteristics,
    including forces, speeds, volumes, rod buckling analysis, and inverse calculations
    (pressure for a given force, diameter for a given force/pressure).

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
        self.setObjectName("CylinderCalculatorWidget")


        self.history_manager = history_manager if history_manager else HistoryManager()
        self.parent_main_calc_widget = parent

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        # --- Main Input Group ---
        input_group = QGroupBox("Paramètres d'entrée du Vérin (Performances)")
        input_group.setObjectName("inputGroupCylinder")
        form_layout = QFormLayout(input_group)
        form_layout.setSpacing(8)

        self.diameter_input = QLineEdit(self); self.diameter_input.setPlaceholderText("mm"); self.diameter_input.setToolTip("Diamètre intérieur du cylindre (D)")
        self.stroke_input = QLineEdit(self); self.stroke_input.setPlaceholderText("mm"); self.stroke_input.setToolTip("Course du piston (S)")
        self.pressure_input = QLineEdit(self); self.pressure_input.setPlaceholderText("bar"); self.pressure_input.setToolTip("Pression hydraulique appliquée (P)")
        self.rod_diameter_input = QLineEdit(self); self.rod_diameter_input.setPlaceholderText("mm (0 si simple effet)"); self.rod_diameter_input.setToolTip("Diamètre de la tige (d). 0 si simple effet.")
        self.flow_rate_input = QLineEdit(self); self.flow_rate_input.setPlaceholderText("L/min (optionnel)"); self.flow_rate_input.setToolTip("Débit d'huile (Q), pour calcul de vitesse.")


        form_layout.addRow(QLabel("Diamètre Piston (D):"), self.diameter_input)
        form_layout.addRow(QLabel("Course (S):"), self.stroke_input)
        form_layout.addRow(QLabel("Pression (P):"), self.pressure_input)
        form_layout.addRow(QLabel("Diamètre Tige (d):"), self.rod_diameter_input)
        form_layout.addRow(QLabel("Débit (Q):"), self.flow_rate_input)
        self.layout.addWidget(input_group)

        self.calculate_button = QPushButton("Calculer les Performances")
        self.calculate_button.setObjectName("calculateCylinderButton")
        self.calculate_button.clicked.connect(self.perform_calculations)
        self.layout.addWidget(self.calculate_button, alignment=Qt.AlignCenter)

        # --- Performance Output Group ---
        output_group = QGroupBox("Résultats de Performance du Vérin")
        output_group.setObjectName("resultsGroupCylinder")
        self.results_layout = QGridLayout(output_group)
        self.results_layout.setSpacing(8)
        self.result_labels = {}
        perf_result_keys = ["piston_area", "annular_area", "force_push", "force_pull", "volume_push", "volume_pull", "speed_push", "speed_pull", "time_push", "time_pull", "ratio"]
        for key in perf_result_keys:
            self.result_labels[key] = QLabel("-"); self.result_labels[key].setObjectName("cylinderResultLabel")
            self.result_labels[key].setMinimumWidth(180); self.result_labels[key].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # ... (Populating results_layout as before, condensed for brevity) ...
        self.results_layout.addWidget(QLabel("Surface Piston (Aₚ):"), 0,0); self.results_layout.addWidget(self.result_labels["piston_area"],0,1)
        self.results_layout.addWidget(QLabel("Surface Annulaire (Aₐ):"),1,0); self.results_layout.addWidget(self.result_labels["annular_area"],1,1)
        self.results_layout.addWidget(QLabel("Force Poussée (Fₚ):"),2,0); self.results_layout.addWidget(self.result_labels["force_push"],2,1)
        self.results_layout.addWidget(QLabel("Force Traction (Fₜ):"),3,0); self.results_layout.addWidget(self.result_labels["force_pull"],3,1)
        self.results_layout.addWidget(QLabel("Volume Piston (Vₚ):"),4,0); self.results_layout.addWidget(self.result_labels["volume_push"],4,1)
        self.results_layout.addWidget(QLabel("Volume Annulaire (Vₐ):"),5,0); self.results_layout.addWidget(self.result_labels["volume_pull"],5,1)
        self.results_layout.addWidget(QLabel("Vitesse Poussée (vₚ):"),0,2); self.results_layout.addWidget(self.result_labels["speed_push"],0,3)
        self.results_layout.addWidget(QLabel("Vitesse Traction (vₜ):"),1,2); self.results_layout.addWidget(self.result_labels["speed_pull"],1,3)
        self.results_layout.addWidget(QLabel("Temps Poussée (tₚ):"),2,2); self.results_layout.addWidget(self.result_labels["time_push"],2,3)
        self.results_layout.addWidget(QLabel("Temps Traction (tₜ):"),3,2); self.results_layout.addWidget(self.result_labels["time_pull"],3,3)
        self.results_layout.addWidget(QLabel("Ratio (φ = Aₚ/Aₐ):"),4,2); self.results_layout.addWidget(self.result_labels["ratio"],4,3)
        self.results_layout.setColumnStretch(1,1); self.results_layout.setColumnStretch(3,1)

        self.layout.addWidget(output_group)

        # --- Buckling Calculation Group ---
        buckling_group = QGroupBox("Calcul de Flambage de la Tige")
        buckling_group.setObjectName("bucklingGroupCylinder")
        buckling_form_layout = QFormLayout(buckling_group)
        self.longueur_libre_tige_input = QLineEdit(self); self.longueur_libre_tige_input.setPlaceholderText("mm"); self.longueur_libre_tige_input.setToolTip("Longueur de la tige non supportée (L).")
        self.coeff_extremite_input = QComboBox(self); self.coeff_extremite_input.setToolTip("Coefficient K pour L_eff = K*L.")
        self.coeff_extremite_input.addItems(["Articulé - Articulé (K=1.0)", "Encastré - Encastré (K=0.5)", "Encastré - Articulé (K=0.7)", "Encastré - Libre (K=2.0)"])
        self.coeff_extremite_input.setItemData(0, 1.0); self.coeff_extremite_input.setItemData(1, 0.5); self.coeff_extremite_input.setItemData(2, 0.7); self.coeff_extremite_input.setItemData(3, 2.0)
        self.module_young_input = QLineEdit(self); self.module_young_input.setPlaceholderText("GPa (ex: 210)"); self.module_young_input.setText("210"); self.module_young_input.setToolTip("Module d'Young (E).")
        self.safety_factor_buckling_input = QLineEdit(self); self.safety_factor_buckling_input.setPlaceholderText("ex: 3.0"); self.safety_factor_buckling_input.setText("3.0"); self.safety_factor_buckling_input.setToolTip("Facteur de sécurité.")

        buckling_form_layout.addRow(QLabel("Longueur Libre Tige (L):"), self.longueur_libre_tige_input)
        buckling_form_layout.addRow(QLabel("Coeff. Fixation (K):"), self.coeff_extremite_input)
        buckling_form_layout.addRow(QLabel("Module d'Young (E):"), self.module_young_input)
        buckling_form_layout.addRow(QLabel("Facteur Sécurité (FS):"), self.safety_factor_buckling_input)
        self.result_labels["force_critique_flambage"] = QLabel("-"); self.result_labels["force_critique_flambage"].setObjectName("cylinderResultLabel")
        self.result_labels["charge_adm_flambage"] = QLabel("-"); self.result_labels["charge_adm_flambage"].setObjectName("cylinderResultLabel")
        self.buckling_warning_label = QLabel(""); self.buckling_warning_label.setObjectName("bucklingWarningLabel"); self.buckling_warning_label.setVisible(False); self.buckling_warning_label.setWordWrap(True)
        buckling_form_layout.addRow(QLabel("Force Critique Flambage (F_crit):"), self.result_labels["force_critique_flambage"])
        buckling_form_layout.addRow(QLabel("Charge Adm. Flambage (F_adm):"), self.result_labels["charge_adm_flambage"])
        buckling_form_layout.addRow(self.buckling_warning_label)
        self.layout.addWidget(buckling_group)

        # --- Inverse Calculation: Pressure for Force ---
        inv_pressure_group = QGroupBox("Calculer Pression pour Force Donnée")
        inv_pressure_group.setObjectName("inverseCalcGroupCylinder")
        inv_pressure_form = QFormLayout(inv_pressure_group)
        self.inv_force_req_input = QLineEdit(self); self.inv_force_req_input.setPlaceholderText("N"); self.inv_force_req_input.setToolTip("Force de poussée désirée.")
        self.inv_piston_dia_for_pressure_input = QLineEdit(self); self.inv_piston_dia_for_pressure_input.setPlaceholderText("mm"); self.inv_piston_dia_for_pressure_input.setToolTip("Diamètre du piston existant.")
        # self.inv_rod_dia_for_pressure_input = QLineEdit(self) # Optional for pull force
        self.result_labels["pressure_req"] = QLabel("-"); self.result_labels["pressure_req"].setObjectName("cylinderResultLabel")
        self.calculate_req_pressure_button = QPushButton("Calculer Pression Requise"); self.calculate_req_pressure_button.setObjectName("calculateInverseButton")
        inv_pressure_form.addRow(QLabel("Force Poussée Désirée (F):"), self.inv_force_req_input)
        inv_pressure_form.addRow(QLabel("Diamètre Piston (D):"), self.inv_piston_dia_for_pressure_input)
        inv_pressure_form.addRow(self.calculate_req_pressure_button)
        inv_pressure_form.addRow(QLabel("Pression Requise (P):"), self.result_labels["pressure_req"])
        self.layout.addWidget(inv_pressure_group)

        # --- Inverse Calculation: Diameter for Force/Pressure ---
        inv_diameter_group = QGroupBox("Calculer Diamètre Piston pour Force/Pression")
        inv_diameter_group.setObjectName("inverseCalcGroupCylinder")
        inv_diameter_form = QFormLayout(inv_diameter_group)
        self.inv_force_for_dia_input = QLineEdit(self); self.inv_force_for_dia_input.setPlaceholderText("N"); self.inv_force_for_dia_input.setToolTip("Force de poussée désirée.")
        self.inv_pressure_avail_input = QLineEdit(self); self.inv_pressure_avail_input.setPlaceholderText("bar"); self.inv_pressure_avail_input.setToolTip("Pression disponible dans le système.")
        self.result_labels["piston_dia_req"] = QLabel("-"); self.result_labels["piston_dia_req"].setObjectName("cylinderResultLabel")
        self.calculate_req_diameter_button = QPushButton("Calculer Diamètre Requis"); self.calculate_req_diameter_button.setObjectName("calculateInverseButton")
        inv_diameter_form.addRow(QLabel("Force Poussée Désirée (F):"), self.inv_force_for_dia_input)
        inv_diameter_form.addRow(QLabel("Pression Disponible (P):"), self.inv_pressure_avail_input)
        inv_diameter_form.addRow(self.calculate_req_diameter_button)
        inv_diameter_form.addRow(QLabel("Ø Piston Requis (D_min):"), self.result_labels["piston_dia_req"])
        self.layout.addWidget(inv_diameter_group)

        self.layout.addStretch()

        self.last_calculated_push_force_N = 0.0
        self.setup_connections()


    def setup_connections(self):
        """Connects signals to slots for dynamic updates and calculations."""
        self.calculate_button.clicked.connect(self.perform_calculations) # Main performance calc
        # Buckling dynamic updates
        for line_edit in [self.longueur_libre_tige_input, self.module_young_input, self.safety_factor_buckling_input, self.rod_diameter_input]:
            line_edit.textChanged.connect(self.perform_buckling_calculation_if_possible)
        self.coeff_extremite_input.currentIndexChanged.connect(self.perform_buckling_calculation_if_possible)
        self.rod_diameter_input.textChanged.connect(self.clear_buckling_results_on_rod_dia_change) # Also clears/updates buckling

        # Inverse calculations
        self.calculate_req_pressure_button.clicked.connect(self.calculate_pressure_for_force)
        self.calculate_req_diameter_button.clicked.connect(self.calculate_diameter_for_force_pressure)


    def clear_buckling_results_on_rod_dia_change(self):
        # ... (implementation as before)
        if "force_critique_flambage" in self.result_labels:
            self.result_labels["force_critique_flambage"].setText("-")
            self.result_labels["charge_adm_flambage"].setText("-")
            if hasattr(self, 'buckling_warning_label'): self.buckling_warning_label.setVisible(False)
        self.perform_buckling_calculation_if_possible()

    def get_float_value(self, line_edit, allow_zero=False, field_name="ce champ"):
        # ... (implementation as before, ensure tooltips are used for field_name)
        try:
            true_field_name = line_edit.toolTip() if line_edit.toolTip() else field_name
            val_str = line_edit.text().strip().replace(',', '.')
            if not val_str:
                if allow_zero and line_edit in [self.rod_diameter_input, self.flow_rate_input,
                                 self.longueur_libre_tige_input, self.module_young_input,
                                 self.safety_factor_buckling_input]:
                    return 0.0
                QMessageBox.warning(self, "Entrée Manquante", f"Le champ '{true_field_name}' est requis.")
                return None
            val = float(val_str)
            if val < 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{true_field_name}' ne peut pas être négative.")
                return None
            if not allow_zero and val == 0:
                QMessageBox.warning(self, "Valeur Incorrecte", f"La valeur pour '{true_field_name}' doit être positive (non nulle).")
                return None
            return val
        except ValueError:
            QMessageBox.warning(self, "Entrée Invalide", f"Veuillez entrer une valeur numérique valide pour '{true_field_name}'.")
            return None


    def perform_calculations(self):
        # ... (implementation as before, ensure it calls perform_buckling_calculation_if_possible at the end)
        # Reset previous results including buckling
        for key in self.result_labels:
            if key not in ["pressure_req", "piston_dia_req"]: # Don't clear inverse results here
                self.result_labels[key].setText("-")
        if hasattr(self, 'buckling_warning_label'): self.buckling_warning_label.setVisible(False)
        self.last_calculated_push_force_N = 0.0

        dia_piston_mm = self.get_float_value(self.diameter_input)
        stroke_mm = self.get_float_value(self.stroke_input)
        pressure_bar = self.get_float_value(self.pressure_input)
        dia_rod_mm = self.get_float_value(self.rod_diameter_input, allow_zero=True)
        flow_lpm = self.get_float_value(self.flow_rate_input, allow_zero=True)

        required_fields_for_perf = { "Diamètre Piston (D)": dia_piston_mm, "Course (S)": stroke_mm, "Pression (P)": pressure_bar}
        for name, val in required_fields_for_perf.items():
            if val is None: return
        if dia_rod_mm is None: dia_rod_mm = 0.0
        if flow_lpm is None: flow_lpm = 0.0
        if dia_rod_mm >= dia_piston_mm and dia_piston_mm > 0 :
            QMessageBox.warning(self, "Entrée Invalide", "Le diamètre de la tige doit être inférieur au diamètre du piston."); return


        area_piston_mm2 = math.pi * (dia_piston_mm / 2)**2
        self.result_labels["piston_area"].setText(f"{area_piston_mm2:.2f} mm² ({area_piston_mm2/100:.2f} cm²)")
        area_rod_mm2 = math.pi * (dia_rod_mm / 2)**2 if dia_rod_mm > 0 else 0
        area_annular_mm2 = area_piston_mm2 - area_rod_mm2
        self.result_labels["annular_area"].setText(f"{area_annular_mm2:.2f} mm² ({area_annular_mm2/100:.2f} cm²)" if dia_rod_mm > 0 else "N/A")
        pressure_N_mm2 = pressure_bar * BAR_TO_N_MM2
        force_push_N = area_piston_mm2 * pressure_N_mm2
        self.result_labels["force_push"].setText(f"{force_push_N:.2f} N ({force_push_N * N_TO_KGF:.2f} kgf)")
        self.last_calculated_push_force_N = force_push_N
        force_pull_N_val = area_annular_mm2 * pressure_N_mm2 if dia_rod_mm > 0 else 0
        self.result_labels["force_pull"].setText(f"{force_pull_N_val:.2f} N ({force_pull_N_val * N_TO_KGF:.2f} kgf)" if dia_rod_mm > 0 else "N/A")
        # ... (rest of performance calculations: volume, ratio, speed, time)
        vol_push_mm3 = area_piston_mm2 * stroke_mm
        self.result_labels["volume_push"].setText(f"{vol_push_mm3 / 1000:.2f} cm³ ({vol_push_mm3 / 1000000:.3f} L)")
        vol_pull_mm3 = area_annular_mm2 * stroke_mm if dia_rod_mm > 0 else 0
        self.result_labels["volume_pull"].setText(f"{vol_pull_mm3 / 1000:.2f} cm³ ({vol_pull_mm3 / 1000000:.3f} L)" if dia_rod_mm > 0 else "N/A")

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

        inputs_summary = f"D:{dia_piston_mm},S:{stroke_mm},P:{pressure_bar},d:{dia_rod_mm},Q:{flow_lpm}"
        results_summary = f"Fp:{self.last_calculated_push_force_N:.0f}N"
        self._log_history("Vérin Perf.", inputs_summary, results_summary)
        self.perform_buckling_calculation_if_possible()

    def perform_buckling_calculation_if_possible(self):
        # ... (implementation as before)
        if "force_critique_flambage" not in self.result_labels: return
        self.result_labels["force_critique_flambage"].setText("-"); self.result_labels["charge_adm_flambage"].setText("-")
        if hasattr(self, 'buckling_warning_label'): self.buckling_warning_label.setVisible(False)
        longueur_libre_mm = self.get_float_value(self.longueur_libre_tige_input, allow_zero=True)
        module_young_gpa = self.get_float_value(self.module_young_input, allow_zero=True)
        safety_factor = self.get_float_value(self.safety_factor_buckling_input, allow_zero=True)
        dia_rod_mm_buckling = self.get_float_value(self.rod_diameter_input, allow_zero=True)
        if not all(x is not None and x > 0 for x in [longueur_libre_mm, module_young_gpa, safety_factor, dia_rod_mm_buckling]):
            if dia_rod_mm_buckling is not None and dia_rod_mm_buckling <=0: self.result_labels["force_critique_flambage"].setText("Ø tige > 0 requis")
            return
        k_factor = self.coeff_extremite_input.currentData()

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
                 self.buckling_warning_label.setText(f"AVERTISSEMENT: F_adm flambage ({F_adm_N:.0f}N) proche de F_poussée.")
                 self.buckling_warning_label.setVisible(True)
        inputs_buckling_summary = f"L:{longueur_libre_mm},K:{k_factor},E:{module_young_gpa},FS:{safety_factor},d_rod:{dia_rod_mm_buckling}"
        results_buckling_summary = f"F_crit:{F_crit_N:.0f}N;F_adm:{F_adm_N:.0f}N"
        self._log_history("Vérin Flambage", inputs_buckling_summary, results_buckling_summary)

    def calculate_pressure_for_force(self):
        """Calculates required pressure for a given push force and piston diameter."""
        self.result_labels["pressure_req"].setText("-")
        force_N = self.get_float_value(self.inv_force_req_input, field_name="Force Poussée Désirée")
        piston_dia_mm = self.get_float_value(self.inv_piston_dia_for_pressure_input, field_name="Diamètre Piston")
        if force_N is None or piston_dia_mm is None: return
        if piston_dia_mm == 0: QMessageBox.warning(self, "Erreur", "Diamètre piston ne peut être zéro."); return

        area_piston_mm2 = math.pi * (piston_dia_mm / 2)**2
        if area_piston_mm2 == 0: QMessageBox.warning(self, "Erreur", "Aire piston nulle."); return # Should be caught by piston_dia_mm > 0

        pressure_N_mm2 = force_N / area_piston_mm2
        pressure_bar_req = pressure_N_mm2 * N_MM2_TO_BAR
        self.result_labels["pressure_req"].setText(f"{pressure_bar_req:.2f} bar ({pressure_N_mm2:.2f} MPa)")

        inputs_summary = f"F_req:{force_N}N, D_piston:{piston_dia_mm}mm"
        results_summary = f"P_req:{pressure_bar_req:.2f}bar"
        self._log_history("Vérin Pression Requis", inputs_summary, results_summary)

    def calculate_diameter_for_force_pressure(self):
        """Calculates required piston diameter for a given push force and available pressure."""
        self.result_labels["piston_dia_req"].setText("-")
        force_N = self.get_float_value(self.inv_force_for_dia_input, field_name="Force Poussée Désirée")
        pressure_bar_avail = self.get_float_value(self.inv_pressure_avail_input, field_name="Pression Disponible")
        if force_N is None or pressure_bar_avail is None: return
        if pressure_bar_avail == 0: QMessageBox.warning(self, "Erreur", "Pression disponible ne peut être zéro."); return

        pressure_N_mm2_avail = pressure_bar_avail * BAR_TO_N_MM2
        if pressure_N_mm2_avail == 0: QMessageBox.warning(self, "Erreur", "Pression disponible (N/mm²) nulle."); return

        required_area_mm2 = force_N / pressure_N_mm2_avail
        # Area = pi * (D/2)^2 = pi * D^2 / 4  => D^2 = 4 * Area / pi => D = sqrt(4 * Area / pi)
        required_diameter_mm = math.sqrt((4 * required_area_mm2) / math.pi)
        self.result_labels["piston_dia_req"].setText(f"{required_diameter_mm:.2f} mm")

        inputs_summary = f"F_req:{force_N}N, P_avail:{pressure_bar_avail}bar"
        results_summary = f"D_req:{required_diameter_mm:.2f}mm"
        self._log_history("Vérin Diamètre Requis", inputs_summary, results_summary)

    def _log_history(self, calc_type, inputs_summary, results_summary):
        """Helper method to log history entries."""
        user_id = "standalone_user" # Default for standalone
        if hasattr(self.parent_main_calc_widget, 'get_current_user_id'):
            user_id = self.parent_main_calc_widget.get_current_user_id()

        if hasattr(self.parent_main_calc_widget, 'add_to_history'):
            self.parent_main_calc_widget.add_to_history(calc_type, inputs_summary, results_summary)
        elif self.history_manager: # Fallback if parent doesn't have the method (e.g. standalone test)
             self.history_manager.add_entry(
                calculator_type=calc_type,
                expression=inputs_summary,
                result=results_summary,
                user_id=user_id
            )

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QScrollArea, QWidget as QBaseWidget
    import sys, os
    app = QApplication(sys.argv)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss: app.setStyleSheet(f.read())
    except Exception as e: print(f"WARNING (CylinderCalculatorWidget Test): Could not load QSS. {e}")

    class MockMainApp(QBaseWidget):
        def __init__(self):
            super().__init__()
            self.user_id = "test_cyl_user_standalone"
            self.history_manager_instance = HistoryManager(db_session_factory=None)
        def add_to_history(self, calc_type, expression, result):
            print(f"HISTORY (Mock): User:{self.user_id}, Type='{calc_type}', Expr='{expression}', Res='{result}'")
            self.history_manager_instance.add_entry(calc_type, expression, result, self.user_id)
        def get_current_user_id(self): return self.user_id

    scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
    calc_widget_container = QBaseWidget(); main_container_layout = QVBoxLayout(calc_widget_container)
    mock_parent = MockMainApp()
    calc = CylinderCalculatorWidget(parent=mock_parent, history_manager=mock_parent.history_manager_instance)
    main_container_layout.addWidget(calc); calc_widget_container.setLayout(main_container_layout)
    scroll_area.setWidget(calc_widget_container)
    scroll_area.setWindowTitle("Calculatrice de Vérins Hydrauliques - Test Avancé"); scroll_area.setMinimumSize(700, 850); scroll_area.show()

    sys.exit(app.exec_())
