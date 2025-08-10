# Widget and logic for the Unit Converter Calculator

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QHBoxLayout,
                             QSizePolicy)
from PyQt5.QtCore import Qt

class UnitConverterCalculatorWidget(QWidget):
    """
    A QWidget that provides unit conversion functionalities across various categories
    like Length, Mass, Pressure, Force, Volume, Temperature, Surface, Speed, and Power.
    Users can select a category, input a value in a source unit, and see the
    converted value in a target unit. Conversions happen dynamically.
    Styling is intended to be applied via QSS through objectNames.
    """
    def __init__(self, parent=None):
        """
        Initializes the UnitConverterCalculatorWidget.
        Args:
            parent: The parent widget.
        """
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignTop)

        # --- Category Selection ---
        self.category_combo = QComboBox(self)
        self.category_combo.setObjectName("categoryComboUnitConverter")
        # self.category_combo.setStyleSheet("font-size: 14px; padding: 5px;") # From QSS
        self.category_combo.currentIndexChanged.connect(self.update_unit_combos)
        self.layout.addWidget(QLabel("Type de Grandeur:")) # This QLabel can inherit general style
        self.layout.addWidget(self.category_combo)

        # --- Conversion Row ---
        conversion_layout = QHBoxLayout()

        # From Unit
        from_unit_layout = QVBoxLayout()
        self.from_value_input = QLineEdit(self)
        self.from_value_input.setObjectName("fromValueInputUnitConverter")
        self.from_value_input.setPlaceholderText("Valeur à convertir")
        # self.from_value_input.setStyleSheet("font-size: 14px; padding: 5px;") # From QSS
        self.from_value_input.textChanged.connect(self.perform_conversion)
        self.from_unit_combo = QComboBox(self)
        self.from_unit_combo.setObjectName("fromUnitComboUnitConverter")
        # self.from_unit_combo.setStyleSheet("font-size: 14px; padding: 5px;") # From QSS
        self.from_unit_combo.currentIndexChanged.connect(self.perform_conversion)
        from_unit_layout.addWidget(self.from_value_input)
        from_unit_layout.addWidget(self.from_unit_combo)
        conversion_layout.addLayout(from_unit_layout)

        # Equals Label
        equals_label = QLabel("=")
        equals_label.setObjectName("unitConverterEqualsLabel")
        # equals_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 0 10px;") # From QSS
        conversion_layout.addWidget(equals_label, alignment=Qt.AlignCenter)

        # To Unit
        to_unit_layout = QVBoxLayout()
        self.to_value_display = QLineEdit(self)
        self.to_value_display.setObjectName("toValueDisplayUnitConverter")
        self.to_value_display.setReadOnly(True)
        # self.to_value_display.setStyleSheet("font-size: 14px; padding: 5px; background-color: #e9e9e9;") # From QSS
        self.to_unit_combo = QComboBox(self)
        self.to_unit_combo.setObjectName("toUnitComboUnitConverter")
        # self.to_unit_combo.setStyleSheet("font-size: 14px; padding: 5px;") # From QSS
        self.to_unit_combo.currentIndexChanged.connect(self.perform_conversion)
        to_unit_layout.addWidget(self.to_value_display)
        to_unit_layout.addWidget(self.to_unit_combo)
        conversion_layout.addLayout(to_unit_layout)

        self.layout.addLayout(conversion_layout)
        self.layout.addStretch()

        self.conversion_factors = self.get_conversion_data()
        self.populate_categories()

        # self.setStyleSheet(...) # Removed, handled by MainCalculatorWidget loading global QSS for the module

    def get_conversion_data(self):
        """
        Defines the conversion factors for various units within categories.
        For most units, the value is a factor to convert from that unit to a common base unit for the category.
        For Temperature, specific string identifiers are used for custom logic.
        Returns:
            dict: A dictionary પાણીof categories, each containing units and their conversion data.
        """
        # Base unit for each category is the one with factor 1.0 (e.g. Meter for Length)
        # For temperature, special handling is needed, so values are identifiers.
        data = {
            "Longueur": {
                "Mètre (m)": 1.0,
                "Millimètre (mm)": 0.001,
                "Centimètre (cm)": 0.01,
                "Kilomètre (km)": 1000.0,
                "Pouce (in)": 0.0254,
                "Pied (ft)": 0.3048,
                "Yard (yd)": 0.9144,
                "Mile (mi)": 1609.34,
            },
            "Masse": {
                "Kilogramme (kg)": 1.0,
                "Gramme (g)": 0.001,
                "Milligramme (mg)": 0.000001,
                "Tonne (t)": 1000.0,
                "Livre (lb)": 0.453592,
                "Once (oz)": 0.0283495,
            },
            "Pression": {
                "Pascal (Pa)": 1.0,
                "Bar (bar)": 100000.0,
                "Millibar (mbar)": 100.0,
                "Atmosphère standard (atm)": 101325.0,
                "PSI (lb/in²)": 6894.76,
                "kPa (kilopascal)": 1000.0,
                "MPa (mégapascal)": 1000000.0,
                "kgf/cm²": 98066.5
            },
            "Force": {
                "Newton (N)": 1.0,
                "kilonewton (kN)": 1000.0,
                "dyne (dyn)": 0.00001,
                "Kilogramme-force (kgf)": 9.80665,
                "Livre-force (lbf)": 4.44822,
            },
            "Volume": {
                "Mètre cube (m³)": 1.0,
                "Litre (L)": 0.001,
                "Millilitre (mL)": 0.000001,
                "Centimètre cube (cm³)": 0.000001,
                "Pouce cube (in³)": 0.0000163871,
                "Pied cube (ft³)": 0.0283168,
                "Gallon US (gal)": 0.00378541,
            },
            "Température": { # Special handling
                "Celsius (°C)": "celsius",
                "Fahrenheit (°F)": "fahrenheit",
                "Kelvin (K)": "kelvin",
            },
            "Surface": {
                "Mètre carré (m²)": 1.0,
                "Centimètre carré (cm²)": 0.0001,
                "Millimètre carré (mm²)": 0.000001,
                "Kilomètre carré (km²)": 1000000.0,
                "Pouce carré (in²)": 0.00064516,
                "Pied carré (ft²)": 0.092903,
                "Hectare (ha)": 10000.0,
                "Acre (acre)": 4046.86,
            },
            "Vitesse": {
                "Mètre par seconde (m/s)": 1.0,
                "Kilomètre par heure (km/h)": 1 / 3.6,
                "Mile par heure (mph)": 0.44704,
                "Pied par seconde (ft/s)": 0.3048,
                "Noeud (knot)": 0.514444, # Nautical mile per hour
            },
            "Puissance": {
                "Watt (W)": 1.0,
                "Kilowatt (kW)": 1000.0,
                "Mégawatt (MW)": 1000000.0,
                "Cheval-vapeur (hp)": 745.7, # Mechanical horsepower
                "Cheval-vapeur métrique (PS)": 735.49875,
                "BTU/heure (BTU/hr)": 0.293071,
            },
            # Add more categories like Débit, Couple etc. later
        }
        return data

    def populate_categories(self):
        self.category_combo.addItems(self.conversion_factors.keys())
        if self.conversion_factors: # Select first category by default
            self.update_unit_combos(0)

    def update_unit_combos(self, index):
        category = self.category_combo.currentText()
        if not category: return

        self.from_unit_combo.clear()
        self.to_unit_combo.clear()

        units = self.conversion_factors.get(category, {})
        if units:
            unit_names = list(units.keys())
            self.from_unit_combo.addItems(unit_names)
            self.to_unit_combo.addItems(unit_names)

        self.perform_conversion() # Recalculate with new units

    def perform_conversion(self):
        category = self.category_combo.currentText()
        from_unit_text = self.from_unit_combo.currentText()
        to_unit_text = self.to_unit_combo.currentText()

        try:
            value_str = self.from_value_input.text().strip().replace(',', '.')
            if not value_str:
                self.to_value_display.setText("")
                return
            from_value = float(value_str)
        except ValueError:
            self.to_value_display.setText("Entrée invalide")
            return

        if not category or not from_unit_text or not to_unit_text:
            self.to_value_display.setText("")
            return

        units_in_category = self.conversion_factors.get(category, {})

        if category == "Température":
            # Special temperature conversion logic
            # From Kelvin: C = K - 273.15; F = (K - 273.15) * 9/5 + 32
            # To Kelvin: C + 273.15; (F - 32) * 5/9 + 273.15

            # Convert input to Kelvin first (base unit for temp logic)
            value_in_kelvin = 0
            if from_unit_text == "Celsius (°C)":
                value_in_kelvin = from_value + 273.15
            elif from_unit_text == "Fahrenheit (°F)":
                value_in_kelvin = (from_value - 32) * 5/9 + 273.15
            elif from_unit_text == "Kelvin (K)":
                value_in_kelvin = from_value
            else:
                self.to_value_display.setText("Erreur Unité Temp")
                return

            # Convert from Kelvin to target unit
            converted_value = 0
            if to_unit_text == "Celsius (°C)":
                converted_value = value_in_kelvin - 273.15
            elif to_unit_text == "Fahrenheit (°F)":
                converted_value = (value_in_kelvin - 273.15) * 9/5 + 32
            elif to_unit_text == "Kelvin (K)":
                converted_value = value_in_kelvin
            else:
                self.to_value_display.setText("Erreur Unité Temp")
                return

            self.to_value_display.setText(f"{converted_value:.4g}")

        else: # Standard factor-based conversion
            from_factor = units_in_category.get(from_unit_text)
            to_factor = units_in_category.get(to_unit_text)

            if from_factor is None or to_factor is None:
                self.to_value_display.setText("Erreur facteur")
                return

            # Convert to base unit, then to target unit
            value_in_base_unit = from_value * from_factor
            converted_value = value_in_base_unit / to_factor

            self.to_value_display.setText(f"{converted_value:.6g}") # Use .6g for general precision

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
            print(f"INFO (UnitConverterCalculatorWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (UnitConverterCalculatorWidget Test): Could not load QSS. {e}")
    # --- End Load QSS ---

    calc = UnitConverterCalculatorWidget()
    calc.setObjectName("UnitConverterCalculatorWidget") # For QSS
    calc.setWindowTitle("Calculatrice de Conversion d'Unités - Test")
    calc.resize(450, 300) # Slightly larger for better viewing
    calc.show()

    # Example programmatic test (more for logic than UI)
    # print("\nProgrammatic Conversion Tests:")
    # # Test Length: 10 ft to m
    # calc.category_combo.setCurrentText("Longueur")
    # calc.from_unit_combo.setCurrentText("Pied (ft)")
    # calc.to_unit_combo.setCurrentText("Mètre (m)")
    # calc.from_value_input.setText("10")
    # print(f"10 ft to m: Expected approx 3.048, Got: {calc.to_value_display.text()}")
    # assert abs(float(calc.to_value_display.text()) - 3.048) < 0.0001

    # # Test Temperature: 32 F to C
    # calc.category_combo.setCurrentText("Température")
    # calc.from_unit_combo.setCurrentText("Fahrenheit (°F)")
    # calc.to_unit_combo.setCurrentText("Celsius (°C)")
    # calc.from_value_input.setText("32")
    # print(f"32 F to C: Expected 0, Got: {calc.to_value_display.text()}")
    # assert abs(float(calc.to_value_display.text()) - 0.0) < 0.0001

    # # Test Pressure: 1 bar to PSI
    # calc.category_combo.setCurrentText("Pression")
    # calc.from_unit_combo.setCurrentText("Bar (bar)")
    # calc.to_unit_combo.setCurrentText("PSI (lb/in²)")
    # calc.from_value_input.setText("1")
    # # 1 bar = 100000 Pa, 1 PSI = 6894.76 Pa. So 1 bar = 100000/6894.76 PSI
    # expected_psi = 100000 / 6894.76
    # print(f"1 bar to PSI: Expected approx {expected_psi:.4f}, Got: {calc.to_value_display.text()}")
    # assert abs(float(calc.to_value_display.text()) - expected_psi) < 0.01

    sys.exit(app.exec_())
