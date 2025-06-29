# Widget and logic for the Commercial Calculator

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize
from .history_manager import HistoryManager # Assuming history_manager is in the same directory

class CommercialCalculatorWidget(QWidget):
    """
    A QWidget implementing a commercial calculator with basic arithmetic operations,
    percentage, sign change, and memory functions (MC, MR, M+, M-).
    It features a dual display for the current expression and the input/result.
    Calculation history is logged via a HistoryManager instance.
    Styling is intended to be applied via QSS through objectNames.
    """
    def __init__(self, parent=None, history_manager=None):
        """
        Initializes the CommercialCalculatorWidget.
        Args:
            parent: The parent widget, typically MainCalculatorWidget. Expected to have an `add_to_history` method.
            history_manager: An instance of HistoryManager for logging calculations. If None, a local instance is created.
        """
        super().__init__(parent)

        self.history_manager = history_manager if history_manager else HistoryManager()
        # self.parent_main_calc_widget = parent # parent() can be used directly if needed.

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5) # Add some spacing

        # Expression display (small, above main display)
        self.expression_display = QLabel("")
        self.expression_display.setObjectName("CalculatorExpressionDisplay")
        self.expression_display.setAlignment(Qt.AlignRight)
        # self.expression_display.setStyleSheet("color: #555; font-size: 14px; padding-right: 5px;") # Style from QSS
        self.layout.addWidget(self.expression_display)

        # Main display for input and results
        self.display = QLineEdit(self)
        self.display.setObjectName("CalculatorDisplay")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setMinimumHeight(60)
        # self.display.setStyleSheet("font-size: 28px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white;") # Style from QSS
        self.layout.addWidget(self.display)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6) # Spacing between buttons, can be adjusted in QSS too
        self.layout.addLayout(self.grid_layout)

        # Define button layout: (text, row, col, rowspan, colspan)
        buttons = [
            ('MC', 0, 0), ('MR', 0, 1), ('M+', 0, 2), ('M-', 0, 3),
            ('C', 1, 0), ('+/-', 1, 1), ('%', 1, 2), ('/', 1, 3),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2), ('*', 2, 3),
            ('4', 3, 0), ('5', 3, 1), ('6', 3, 2), ('-', 3, 3),
            ('1', 4, 0), ('2', 4, 1), ('3', 4, 2), ('+', 4, 3),
            ('0', 5, 0, 1, 2), ('.', 5, 2), ('=', 5, 3)
        ]

        self.button_widgets = {}

        for i, btn_def in enumerate(buttons):
            btn_text, row, col, *span = btn_def
            button = QPushButton(btn_text)
            from PyQt5.QtWidgets import QSizePolicy

            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # button.setSizePolicy(QPushButton.Expanding, QPushButton.Expanding)
            # button.setMinimumSize(QSize(60, 50)) # Min size will be handled by QSS or default
            # button.setStyleSheet(self.get_button_style(btn_text)) # Styles will come from QSS

            # Set objectName for QSS styling
            if btn_text.isdigit():
                button.setObjectName("calcNumButton")
            elif btn_text == '.':
                button.setObjectName("calcDotButton")
            elif btn_text == '=':
                button.setObjectName("calcEqualsButton")
            elif btn_text == 'C':
                button.setObjectName("calcClearButton")
            elif btn_text in ['/', '*', '-', '+']:
                button.setObjectName("calcOperatorButton")
            elif btn_text in ['MC', 'MR', 'M+', 'M-']:
                button.setObjectName("calcMemoryButton")
            else: # %, +/- or other specific function buttons
                button.setObjectName("calcFunctionButton") # Generic function button or more specific if needed

            button.clicked.connect(self.on_button_clicked)

            if len(span) == 2: # rowspan, colspan
                self.grid_layout.addWidget(button, row, col, span[0], span[1])
            elif len(span) == 1: # colspan (rowspan is 1 by default)
                 self.grid_layout.addWidget(button, row, col, 1, span[0])
            else: # No span
                self.grid_layout.addWidget(button, row, col)
            self.button_widgets[btn_text] = button

        self.current_input = ""
        self.full_expression = ""
        self.memory_value = 0.0
        self.just_evaluated = False

        # self.setStyleSheet(...) # Removed, styles will be loaded globally by MainCalculatorWidget
        # or specific to this widget via its objectName if MainCalculatorWidget applies it to children.

    # get_button_style method is no longer needed as styles are from QSS.

    def on_button_clicked(self):
        """
        Handles click events from all calculator buttons.
        Determines the action based on the button's text and updates the display
        and internal state accordingly.
        """
        button = self.sender()
        text = button.text()

        if self.just_evaluated and text not in ['=', '/', '*', '-', '+', '%', '+/-', 'M+', 'M-', 'MR', 'MC']:
            # If a calculation was just done and a new number is pressed, clear previous input.
            # Operators or memory functions can continue with the result.
            self.current_input = ""
            self.full_expression = ""
            self.just_evaluated = False
        elif self.just_evaluated and text in ['/', '*', '-', '+']:
             self.full_expression = self.current_input # Start new expression with previous result
             self.just_evaluated = False # Allow chaining operations

        if text.isdigit() or (text == '.' and '.' not in self.current_input):
            self.current_input += text
            self.display.setText(self.current_input)
        elif text in ['/', '*', '-', '+']:
            if self.current_input: # Ensure there's something to operate on
                # If the last char in full_expression is an operator, replace it
                if self.full_expression and self.full_expression[-1] in ['/', '*', '-', '+']:
                    self.full_expression = self.full_expression[:-1] + text
                else:
                    self.full_expression += self.current_input + text
                self.current_input = ""
                self.expression_display.setText(self.full_expression)
                self.display.setText("") # Clear main display for next number
        elif text == '=':
            if self.current_input and self.full_expression:
                self.full_expression += self.current_input
                try:
                    # Basic security: replace comma, ensure limited char set
                    # For production, a proper math expression parser is safer than eval.
                    safe_expr = self.full_expression.replace(',', '.')
                    if not all(c in "0123456789.+-*/" for c in safe_expr): # Removed () for basic commercial
                        raise ValueError("Invalid characters in expression")

                    result = eval(safe_expr)
                    # Format result to avoid excessively long floats (e.g. 0.1 + 0.2)
                    if isinstance(result, float) and result == int(result):
                        result_str = str(int(result))
                    else:
                        result_str = f"{result:.10g}" # Limit precision, remove trailing zeros

                    self.display.setText(result_str)

                    # Add to history via parent if available, otherwise local
                    if hasattr(self.parent(), 'add_to_history'):
                         self.parent().add_to_history("Commercial", self.full_expression, result_str)
                    else:
                        self.history_manager.add_entry("Commercial", self.full_expression, result_str)

                    self.expression_display.setText(self.full_expression + " =")
                    self.current_input = result_str # Store result for potential chaining
                    self.full_expression = "" # Reset for next independent calculation start
                    self.just_evaluated = True
                except ZeroDivisionError:
                    self.display.setText("Error: Div by 0")
                    self.current_input = ""
                    self.full_expression = ""
                    self.just_evaluated = True
                except Exception as e:
                    self.display.setText("Error")
                    # print(f"Eval error: {e} on expression: {self.full_expression}") # for debugging
                    self.current_input = ""
                    self.full_expression = ""
                    self.just_evaluated = True
        elif text == 'C':
            self.current_input = ""
            self.full_expression = ""
            self.display.setText("")
            self.expression_display.setText("")
            self.just_evaluated = False
        elif text == '+/-':
            if self.current_input:
                if self.current_input.startswith('-'):
                    self.current_input = self.current_input[1:]
                else:
                    self.current_input = '-' + self.current_input
                self.display.setText(self.current_input)
        elif text == '%':
            if self.current_input and self.full_expression:
                # This is a simple percentage of the first number in the expression or last result
                # e.g. 100 + 10% (of 100) = 110
                # More complex % like "50 * 10%" (meaning 5) needs careful parsing.
                # For now, let's treat it as X current_op (Y/100) * X_prime
                # Example: 200 + 10%  -> full_expression = "200+", current_input = "10"
                # We want 200 + (10/100 * 200) = 220
                try:
                    val = float(self.current_input)
                    # Find the last number in full_expression
                    last_num_str = ""
                    temp_expr = self.full_expression.rstrip('+-*/')
                    for char_idx in range(len(temp_expr) -1, -1, -1):
                        if temp_expr[char_idx] in '+-*/':
                            break
                        last_num_str = temp_expr[char_idx] + last_num_str

                    if not last_num_str: # If full_expression was empty or only result
                        base_val_str = self.current_input if not self.full_expression else self.full_expression.strip('= ')
                        base_val = float(base_val_str)
                        result = base_val * (val / 100)
                    else:
                        base_val = float(last_num_str)
                        percentage_val = base_val * (val / 100)
                        # Now we need to evaluate the expression with this percentage_val
                        # e.g., if full_expression was "200+", and current was "10" (%)
                        # we want to eval "200 + 20"
                        self.full_expression += str(percentage_val)
                        result = eval(self.full_expression.replace(',', '.'))

                    result_str = f"{result:.10g}"
                    self.display.setText(result_str)
                    self.expression_display.setText(self.full_expression + "% =" if not last_num_str else self.full_expression + " =" )
                    self.current_input = result_str
                    self.full_expression = ""
                    self.just_evaluated = True
                except Exception as e:
                    self.display.setText("Error %")
                    # print(f"Percentage error: {e}")
        elif text == 'MC': # Memory Clear
            self.memory_value = 0.0
        elif text == 'MR': # Memory Recall
            self.current_input = str(self.memory_value if self.memory_value != int(self.memory_value) else int(self.memory_value))
            self.display.setText(self.current_input)
            self.just_evaluated = False # Allow editing recalled number
        elif text == 'M+': # Memory Add
            if self.current_input:
                try:
                    self.memory_value += float(self.current_input)
                    self.just_evaluated = True # Treat as an operation, clear display on next digit
                except ValueError:
                    self.display.setText("Error M+")
        elif text == 'M-': # Memory Subtract
            if self.current_input:
                try:
                    self.memory_value -= float(self.current_input)
                    self.just_evaluated = True
                except ValueError:
                    self.display.setText("Error M-")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import os

    # This is a simplified test environment.
    # For proper DB testing, HistoryManager would need a db_session_factory.
    # For UI styling, the main_calculator_widget.py's __main__ block is better
    # as it loads the global QSS for the calculator module.

    app = QApplication(sys.argv)

    # --- Attempt to load QSS for standalone testing ---
    # This makes the standalone test look more like the final product.
    # Assumes this file is in 'calculator/' and QSS in 'calculator/styles/'
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss:
            app.setStyleSheet(f.read())
            print(f"INFO (CommercialCalculatorWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (CommercialCalculatorWidget Test): Could not load QSS. {e}")
    # --- End Load QSS ---

    # Mock parent for history (optional, if direct parent calls are tested)
    class MockMainApp(QWidget):
        def __init__(self):
            super().__init__()
            self.history_log = []
        def add_to_history(self, calc_type, expression, result):
            self.history_log.append({
                "type": calc_type, "expression": expression, "result": result
            })
            print(f"MockMainApp History: {calc_type} - {expression} = {result}")

    mock_parent_app = MockMainApp()

    # Test with a local HistoryManager (no DB persistence in this simple test)
    # To test with DB, HistoryManager needs a db_session_factory.
    # For this standalone test, we'll use its default in-memory behavior if no factory.
    # hm = HistoryManager(db_session_factory=None) # Explicitly None for clarity
    # calc = CommercialCalculatorWidget(parent=mock_parent_app, history_manager=hm)

    # Simpler instantiation for basic UI check without full history manager setup:
    calc = CommercialCalculatorWidget(parent=mock_parent_app)
    calc.setObjectName("CommercialCalculatorWidget") # For QSS

    calc.setWindowTitle("Commercial Calculator Test")
    calc.resize(350, 450)
    calc.show()

    # Example of programmatic interaction for testing logic (not UI based)
    # Note: This requires direct calls to on_button_clicked or helper methods,
    # which is more complex than UI interaction testing.
    # For now, manual UI testing is the primary method via standalone execution.

    # Test case: 12 + 5 * 2 - 1 = 21 (Order of ops is L-to-R without parenthesis here)
    # Or more simply: 12 + 5 = 17
    # calc.button_widgets['1'].click()
    # calc.button_widgets['2'].click()
    # calc.button_widgets['+'].click()
    # calc.button_widgets['5'].click()
    # calc.button_widgets['='].click()
    # assert calc.display.text() == "17"
    # print("Test '12+5=17' passed if display is 17.")


    sys.exit(app.exec_())
