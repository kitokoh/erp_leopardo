# Widget and logic for the Scientific Calculator

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import Qt, QSize
import math
from .history_manager import HistoryManager # Assuming history_manager is in the same directory


class ScientificCalculatorWidget(QWidget):
    """
    A QWidget implementing a scientific calculator with standard arithmetic,
    trigonometric functions (sin, cos, tan, asin, acos, atan), logarithms (log10, ln),
    exponentiation (x^y, e^x, 10^x), square root, factorial, inverse (1/x),
    constants (pi, e), and parenthesis.
    It supports angle modes (Degrees/Radians) and an inverse function mode.
    Features a dual display for expression and input/result.
    Logs calculations via HistoryManager. Styling is via QSS.
    """
    def __init__(self, parent=None, history_manager=None):
        """
        Initializes the ScientificCalculatorWidget.
        Args:
            parent: The parent widget, typically MainCalculatorWidget.
            history_manager: An instance of HistoryManager for logging.
        """
        super().__init__(parent)

        self.history_manager = history_manager if history_manager else HistoryManager()
        # self.parent_main_calc_widget = parent # Use parent() directly

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        # Expression display
        self.expression_display_label = QLabel("")
        self.expression_display_label.setObjectName("CalculatorExpressionDisplay")
        self.expression_display_label.setAlignment(Qt.AlignRight)
        # self.expression_display_label.setStyleSheet(...) # Style from QSS
        self.layout.addWidget(self.expression_display_label)

        # Main display for input and results
        self.display_input = QLineEdit(self)
        self.display_input.setObjectName("CalculatorDisplay")
        self.display_input.setReadOnly(True)
        self.display_input.setAlignment(Qt.AlignRight)
        self.display_input.setMinimumHeight(60)
        # self.display_input.setStyleSheet(...) # Style from QSS
        self.layout.addWidget(self.display_input)

        # Angle mode selector (Degrees/Radians)
        self.angle_mode_selector = QComboBox(self)
        self.angle_mode_selector.setObjectName("sciAngleModeSelector") # For specific styling if needed
        self.angle_mode_selector.addItem("Deg", "degrees")
        self.angle_mode_selector.addItem("Rad", "radians")
        # self.angle_mode_selector.setStyleSheet(...) # Style from QSS
        # self.layout.addWidget(self.angle_mode_selector)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5) # Consistent spacing
        self.layout.addLayout(self.grid_layout)

        # Define button layout: (text, row, col, rowspan, colspan)
        # Column 0: Scientific functions
        # Column 1-4: Standard numbers and ops
        # Column 5: More scientific functions
        buttons = [
            # Row 0: Angle mode, Inv, x!, ( , )
            (self.angle_mode_selector, 0, 0), ('Inv', 0, 1), ('x!', 0, 2), ('(', 0, 3), (')', 0, 4),
            # Row 1: sin, ln, 7, 8, 9, /
            ('sin', 1, 0), ('ln', 1, 1), ('7', 1, 2), ('8', 1, 3), ('9', 1, 4), ('/', 1, 5),
            # Row 2: cos, log, 4, 5, 6, *
            ('cos', 2, 0), ('log', 2, 1), ('4', 2, 2), ('5', 2, 3), ('6', 2, 4), ('*', 2, 5),
            # Row 3: tan, sqrt, 1, 2, 3, -
            ('tan', 3, 0), ('√', 3, 1), ('1', 3, 2), ('2', 3, 3), ('3', 3, 4), ('-', 3, 5),
            # Row 4: e, ^, C, 0, ., +
            ('e', 4, 0), ('xʸ', 4, 1), ('C', 4, 2), ('0', 4, 3), ('.', 4, 4), ('+', 4, 5),
            # Row 5: pi, 1/x, <-- (Backspace), = (span 2 cols)
            ('π', 5, 0), ('1/x', 5, 1), ('←', 5, 2), ('=', 5, 3, 1, 3) # text, row, col, rowspan, colspan
        ]

        self.button_widgets = {}
        self.is_inverse_mode = False # For 'Inv' button functionality

        for i, btn_def in enumerate(buttons):
            if isinstance(btn_def[0], QComboBox): # Handle ComboBox directly
                widget = btn_def[0]
                _, row, col, *span = btn_def
                self.grid_layout.addWidget(widget, row, col)
                continue

            btn_text, row, col, *span_data = btn_def
            button = QPushButton(btn_text)
            button.setSizePolicy(QPushButton.Expanding, QPushButton.Expanding)
            # button.setMinimumSize(QSize(50, 45)) # Style from QSS
            # button.setStyleSheet(self.get_button_style(btn_text)) # Style from QSS

            # Set objectName for QSS styling
            if btn_text.isdigit():
                button.setObjectName("calcNumButton")
            elif btn_text == '.':
                button.setObjectName("calcDotButton")
            elif btn_text == '=':
                button.setObjectName("calcEqualsButton")
            elif btn_text == 'C' or btn_text == '←':
                button.setObjectName("calcClearButton") # Backspace also uses clear styling
            elif btn_text in ['/', '*', '-', '+']:
                button.setObjectName("calcOperatorButton")
            elif btn_text == 'Inv': # Special case for Inv button ID for active state styling
                button.setObjectName("sciInvButton")
            elif btn_text in ['sin', 'cos', 'tan', '√', 'log', 'ln', 'xʸ', 'x!', '1/x', 'π', 'e', '(', ')']:
                button.setObjectName("calcSciFunctionButton")
            else: # Should not happen with current layout
                button.setObjectName("calcFunctionButton")

            button.clicked.connect(self.on_button_clicked)

            if len(span_data) == 2: # rowspan, colspan
                self.grid_layout.addWidget(button, row, col, span_data[0], span_data[1])
            elif len(span_data) == 1: # colspan
                 self.grid_layout.addWidget(button, row, col, 1, span_data[0])
            else: # No span
                self.grid_layout.addWidget(button, row, col)
            self.button_widgets[btn_text] = button # Still useful for dynamic text changes (Inv)

        self.current_display_text = ""
        self.expression_for_eval = ""
        self.just_evaluated = False
        # self.setStyleSheet(...) # Style from QSS loaded by MainCalculatorWidget

    # get_button_style method is no longer needed.

    def on_button_clicked(self):
        """
        Handles click events from all calculator buttons.
        Manages input, expression building, and triggers evaluation or function calls.
        """
        button = self.sender()
        text = button.text()

        if self.just_evaluated and text not in ['=', '/', '*', '-', '+', 'xʸ', 'Inv'] and not (text in ['sin', 'cos', 'tan', '√', 'log', 'ln', 'x!', '1/x'] and not self.current_display_text):
            # If a result is shown and a new number/constant is pressed, clear previous input.
            # Operators, Inv, or functions (if display is empty) can continue/start new.
            self.current_display_text = ""
            self.expression_for_eval = ""
            self.just_evaluated = False
        elif self.just_evaluated and text in ['/', '*', '-', '+', 'xʸ']:
             # Start new expression with previous result if an operator is pressed
             self.expression_for_eval = self.current_display_text
             self.current_display_text = "" # Clear display for next number
             self.just_evaluated = False

        # Handle button clicks
        if text.isdigit() or text == '.':
            if text == '.' and '.' in self.current_display_text: return # Only one decimal point
            self.current_display_text += text
            self.expression_for_eval += text
        elif text == 'C':
            self.current_display_text = ""
            self.expression_for_eval = ""
            self.is_inverse_mode = False # Reset Inv mode
            self.update_inv_button_states()
        elif text == '←': # Backspace
            self.current_display_text = self.current_display_text[:-1]
            # This needs more robust handling for expression_for_eval if functions were involved
            if self.expression_for_eval and not self.expression_for_eval.endswith(')'):
                 self.expression_for_eval = self.expression_for_eval[:-1]
            # A more complex backspace would require tokenizing or smarter string manipulation
        elif text in ['/', '*', '-', '+']:
            if self.current_display_text: # Append current number to expression before operator
                self.expression_for_eval += self.current_display_text
                self.current_display_text = ""
            if self.expression_for_eval and self.expression_for_eval[-1] in ['/', '*', '-', '+']: # Replace last op
                self.expression_for_eval = self.expression_for_eval[:-1] + text
            else:
                self.expression_for_eval += text
        elif text == '(':
            self.expression_for_eval += "("
        elif text == ')':
            if self.current_display_text: # Add current number before closing parenthesis
                 self.expression_for_eval += self.current_display_text
                 self.current_display_text = ""
            self.expression_for_eval += ")"
        elif text == 'π':
            self.current_display_text = str(math.pi)
            self.expression_for_eval += "math.pi"
            self.just_evaluated = True # Treat as a full number input
        elif text == 'e':
            self.current_display_text = str(math.e)
            self.expression_for_eval += "math.e"
            self.just_evaluated = True
        elif text == 'xʸ': # Power
            if self.current_display_text:
                self.expression_for_eval += self.current_display_text
                self.current_display_text = ""
            self.expression_for_eval += "**" # Python's power operator
        elif text == '√': # Square root
             self.handle_function_input("math.sqrt(" if not self.is_inverse_mode else self.current_display_text + "**(1/")
             # For x^3, use x**(1/3), needs closing ')'
        elif text == 'sin':
            self.handle_function_input("math.sin(" if not self.is_inverse_mode else "math.asin(")
        elif text == 'cos':
            self.handle_function_input("math.cos(" if not self.is_inverse_mode else "math.acos(")
        elif text == 'tan':
            self.handle_function_input("math.tan(" if not self.is_inverse_mode else "math.atan(")
        elif text == 'log': # log base 10
            self.handle_function_input("math.log10(" if not self.is_inverse_mode else "10**(")
        elif text == 'ln': # Natural log (log base e)
            self.handle_function_input("math.log(" if not self.is_inverse_mode else "math.exp(")
        elif text == 'x!': # Factorial
            if self.current_display_text:
                self.expression_for_eval += f"math.factorial(int({self.current_display_text}))"
                self.current_display_text = "" # Factorial is usually a final operation on a number
                # Auto-evaluate factorial for simplicity, or make it part of expression
                self.evaluate_expression(is_factorial=True)
                return # Skip display update at the end of this function
        elif text == '1/x': # Inverse
            if self.current_display_text:
                self.expression_for_eval += f"(1/{self.current_display_text})"
                self.current_display_text = ""
                self.evaluate_expression() # Auto-evaluate
                return
        elif text == 'Inv':
            self.is_inverse_mode = not self.is_inverse_mode
            self.update_inv_button_states()
        elif text == '=':
            self.evaluate_expression()

        self.update_display()

    def handle_function_input(self, func_str_eval):
        """Handles input for functions that take arguments e.g. sin(, log( """
        if self.current_display_text: # If there's a number, function applies to it
            # This logic can get complex: e.g. 5+sin(3) vs sin(5+3)
            # Simplest: function applies to the current number or starts a new sub-expression
            self.expression_for_eval += func_str_eval + self.current_display_text
            self.current_display_text = "" # Clear display, expecting ')' or further input
        else: # No current number, just add the function call start
            self.expression_for_eval += func_str_eval

        # If angle mode is degrees for trig functions, add radians conversion
        # This needs to be smarter if func_str_eval already contains math.radians
        if func_str_eval in ["math.sin(", "math.cos(", "math.tan("] and self.angle_mode_selector.currentData() == "degrees":
             # Remove the last '(', add 'math.radians(', then add back the '(' if needed by original func_str_eval
             # This part is tricky with current string building. A token-based system would be better.
             # For now, let's assume direct math.sin(math.radians(input))
             # The expression_for_eval will need to be built carefully.
             # Current simple approach: let eval handle it, but functions must be defined to expect radians
             pass # Will handle angle mode in evaluate_expression for now

    def update_inv_button_states(self):
        """Updates button texts based on Inv mode."""
        self.button_widgets['Inv'].setStyleSheet(self.get_button_style('Inv') + ("background-color: #3F51B5;" if self.is_inverse_mode else "")) # Indigo if active

        # Update texts for functions that have an inverse
        self.button_widgets['sin'].setText("asin" if self.is_inverse_mode else "sin")
        self.button_widgets['cos'].setText("acos" if self.is_inverse_mode else "cos")
        self.button_widgets['tan'].setText("atan" if self.is_inverse_mode else "tan")
        self.button_widgets['log'].setText("10ˣ" if self.is_inverse_mode else "log")
        self.button_widgets['ln'].setText("eˣ" if self.is_inverse_mode else "ln")
        self.button_widgets['√'].setText("x²" if self.is_inverse_mode else "√") # x² is inverse of sqrt for positive x
        # xʸ could become y रूट x (y-th root of x)
        # self.button_widgets['xʸ'].setText("ʸ√x" if self.is_inverse_mode else "xʸ")


    def evaluate_expression(self, is_factorial=False):
        if not self.expression_for_eval and not self.current_display_text:
            return

        # Append any final number from display to expression
        if self.current_display_text:
            self.expression_for_eval += self.current_display_text
            self.current_display_text = ""

        full_expr_for_history = self.expression_for_eval # Save for history

        try:
            # Prepare expression for eval
            eval_expr = self.expression_for_eval

            # Handle angle conversions for trig functions if in degrees mode
            # This is a simplified approach; a proper parser would be more robust.
            if self.angle_mode_selector.currentData() == "degrees":
                for func in ["sin(", "cos(", "tan("]: # asin, acos, atan output in radians
                    # We need to wrap the argument of sin, cos, tan with math.radians()
                    # Example: "math.sin(30)" becomes "math.sin(math.radians(30))"
                    # This is complex with string replacement. A parser/lexer would be better.
                    # For now, we assume functions like math.sin are called with math.radians(arg)
                    # if the function itself does not handle degrees.
                    # Let's assume the functions in `math` (sin, cos, tan) expect radians.
                    # The `handle_function_input` should ideally build this.
                    # For simplicity, if we see "math.sin(", we will assume the argument needs conversion
                    # This is still very naive.
                    start_idx = 0
                    while True:
                        idx = eval_expr.find("math."+func, start_idx)
                        if idx == -1: break

                        open_paren_idx = idx + len("math."+func)
                        # Find the matching closing parenthesis for this function call
                        balance = 1
                        close_paren_idx = -1
                        for i in range(open_paren_idx + 1, len(eval_expr)):
                            if eval_expr[i] == '(': balance += 1
                            elif eval_expr[i] == ')': balance -= 1
                            if balance == 0:
                                close_paren_idx = i
                                break

                        if close_paren_idx != -1:
                            arg = eval_expr[open_paren_idx+1:close_paren_idx]
                            # Avoid double wrapping if math.radians is already there
                            if "math.radians" not in arg:
                                replacement = f"math.{func}math.radians({arg}))"
                                eval_expr = eval_expr[:idx] + replacement + eval_expr[close_paren_idx+1:]
                                start_idx = idx + len(replacement)
                            else:
                                start_idx = close_paren_idx +1
                        else: # Mismatched parenthesis, break to avoid infinite loop
                            break

            # Inverse trig functions (asin, acos, atan) output in radians. Convert to degrees if needed.
            if self.angle_mode_selector.currentData() == "degrees":
                for func in ["asin(", "acos(", "atan("]:
                    if "math."+func in eval_expr: # Check if it's an output that needs conversion
                         # This is also tricky. If "math.degrees(math.asin(...))" is the structure.
                         # Let's assume for now the result of asin/acos/atan is directly converted.
                         # This means the original eval_expr should be `math.degrees(math.asin(x))`
                         # This logic should be in how `handle_function_input` builds `expression_for_eval`
                         pass


            # Replace user-friendly power symbol with Python's
            eval_expr = eval_expr.replace('^', '**') # Should be xʸ button

            # Ensure all functions are `math.` prefixed if not already
            # This is a basic safeguard; a more robust solution is a custom parser.
            # For example, 'sqrt(' should become 'math.sqrt('.
            # This is partially handled by handle_function_input.

            # print(f"Evaluating: {eval_expr}") # Debugging

            # Define a limited scope for eval to enhance security
            # Add math functions to the scope
            allowed_globals = {"math": math, "__builtins__": {}}
            allowed_locals = {} # Could add variables here if needed

            result = eval(eval_expr, allowed_globals, allowed_locals)

            # Convert radians result from inverse trig functions to degrees if mode is Deg
            # This check needs to be specific to the operation that produced the result.
            # This is hard to do post-eval without knowing what the last operation was.
            # It's better if the expression itself is constructed to yield degrees.
            # E.g. expression_for_eval = "math.degrees(math.asin(0.5))"

            # Example: if the last function was asin, acos, atan and mode is degrees
            # This is a heuristic and might not always be correct.
            last_func_call = ""
            if "math.asin(" in full_expr_for_history or \
               "math.acos(" in full_expr_for_history or \
               "math.atan(" in full_expr_for_history:
                if self.angle_mode_selector.currentData() == "degrees":
                    result = math.degrees(result)


            if isinstance(result, float) and result == int(result):
                result_str = str(int(result))
            else:
                result_str = f"{result:.10g}" # Limit precision

            self.current_display_text = result_str
            self.expression_for_eval = result_str # Store result for chaining

            # Add to history
            if hasattr(self.parent(), 'add_to_history'):
                 self.parent().add_to_history("Scientific", full_expr_for_history, result_str)
            else:
                self.history_manager.add_entry("Scientific", full_expr_for_history, result_str)

            self.just_evaluated = True
            self.is_inverse_mode = False # Reset Inv mode after evaluation
            self.update_inv_button_states()

        except ZeroDivisionError:
            self.current_display_text = "Error: Div by 0"
            self.expression_for_eval = ""
            self.just_evaluated = True
        except (SyntaxError, TypeError, ValueError, NameError, AttributeError) as e:
            self.current_display_text = "Error: Syntax"
            # print(f"Scientific Calc Error: {e} on expression: {eval_expr}") # Debug
            self.expression_for_eval = ""
            self.just_evaluated = True
        except Exception as e: # Catch any other math errors etc.
            self.current_display_text = "Error"
            # print(f"Scientific Calc Error: {e} on expression: {eval_expr}") # Debug
            self.expression_for_eval = ""
            self.just_evaluated = True

        if not is_factorial: # Factorial already updates display
            self.update_display()


    def update_display(self):
        self.display_input.setText(self.current_display_text)
        # Show a simplified version of expression_for_eval in the label
        # e.g. replace "math.sqrt" with "sqrt", "math.pi" with "π"
        display_expr = self.expression_for_eval
        display_expr = display_expr.replace("math.sqrt", "sqrt")
        display_expr = display_expr.replace("math.sin", "sin")
        display_expr = display_expr.replace("math.cos", "cos")
        display_expr = display_expr.replace("math.tan", "tan")
        display_expr = display_expr.replace("math.log10", "log")
        display_expr = display_expr.replace("math.log", "ln")
        display_expr = display_expr.replace("math.asin", "asin")
        display_expr = display_expr.replace("math.acos", "acos")
        display_expr = display_expr.replace("math.atan", "atan")
        display_expr = display_expr.replace("math.factorial", "fact")
        display_expr = display_expr.replace("math.pi", "π")
        display_expr = display_expr.replace("math.e", "e")
        display_expr = display_expr.replace("**", "^")
        # Add current number being typed to the expression display if not empty
        if self.current_display_text:
            self.expression_display_label.setText(display_expr + self.current_display_text)
        else:
            self.expression_display_label.setText(display_expr)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QWidget # Added QWidget for MockMainApp
    import sys
    import os

    app = QApplication(sys.argv)

    # --- Attempt to load QSS for standalone testing ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        qss_file_path = os.path.join(script_dir, "styles", "calculator_style.qss")
        with open(qss_file_path, "r") as f_qss:
            app.setStyleSheet(f.read())
            print(f"INFO (ScientificCalculatorWidget Test): Loaded QSS from {qss_file_path}")
    except Exception as e:
        print(f"WARNING (ScientificCalculatorWidget Test): Could not load QSS. {e}")
    # --- End Load QSS ---

    class MockMainApp(QWidget): # Mock parent for history
        def __init__(self):
            super().__init__()
            self.history_log = []
        def add_to_history(self, calc_type, expression, result):
            self.history_log.append({
                "type": calc_type, "expression": expression, "result": result
            })
            print(f"MockMainApp History: {calc_type} - {expression} = {result}")

    mock_parent = MockMainApp()
    calc = ScientificCalculatorWidget(parent=mock_parent)
    calc.setObjectName("ScientificCalculatorWidget") # For QSS

    calc.setWindowTitle("Scientific Calculator Test")
    calc.resize(420, 550) # Adjusted size for more buttons
    calc.show()

    # Example test logic (can be expanded)
    # calc.button_widgets['sin'].click()
    # calc.button_widgets['3'].click()
    # calc.button_widgets['0'].click()
    # calc.button_widgets[')'].click() # Assuming auto-parenthesis or manual for test
    # calc.button_widgets['='].click()
    # Expected: math.sin(math.radians(30)) = 0.5
    # print(f"Test: sin(30 deg) = {calc.display_input.text()}")
    # assert calc.display_input.text() == "0.5"

    sys.exit(app.exec_())
