import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QDialogButtonBox, QMessageBox, QLabel,
                             QDoubleSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional

try:
    from ..cruds import restaurant_commande_crud, restaurant_paiement_crud
    from ..models import RestaurantCommande # For type hinting
except ImportError:
    logging.error("ges_restaurant.ui.payment_dialog: Failed to import CRUDS or Models.")
    restaurant_commande_crud = None
    restaurant_paiement_crud = None


class PaymentDialog(QDialog):
    payment_processed_signal = pyqtSignal(int) # Emits commande_id

    def __init__(self, commande: RestaurantCommande, parent=None):
        super().__init__(parent)
        self.setObjectName("PaymentDialog") # Object name for the dialog
        self.commande = commande

        if not self.commande:
            QMessageBox.critical(self, self.tr("Error"), self.tr("No commande data provided for payment."))
            raise ValueError("PaymentDialog initialized without a commande object.")

        self.setWindowTitle(self.tr("Process Payment for Order ID: {0}").format(self.commande.id))
        self.setMinimumWidth(400)

        self._init_ui()
        self._load_payment_details()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.order_total_label = QLabel(f"{self.commande.total_commande_ttc or 0.0:.2f} €")
        self.order_total_label.setObjectName("orderTotalLabel")
        self.amount_due_label = QLabel()
        self.amount_due_label.setObjectName("amountDueLabel")

        self.amount_paid_spinbox = QDoubleSpinBox()
        self.amount_paid_spinbox.setObjectName("amountPaidSpinBox")
        self.amount_paid_spinbox.setDecimals(2)
        self.amount_paid_spinbox.setRange(0.01, 1000000.00)
        self.amount_paid_spinbox.setSuffix(" €")

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.setObjectName("paymentMethodCombo")
        self.payment_method_combo.addItems([
            self.tr("Cash"),
            self.tr("Credit Card"),
            self.tr("Debit Card"),
            self.tr("Restaurant Voucher"),
            self.tr("Online Payment"),
            self.tr("Other")
        ])

        self.transaction_ref_edit = QLineEdit()
        self.transaction_ref_edit.setObjectName("transactionRefEdit")
        self.transaction_ref_edit.setPlaceholderText(self.tr("e.g., Card transaction ID, Cheque number"))

        form_layout.addRow(self.tr("Total Order Amount (TTC):"), self.order_total_label)
        form_layout.addRow(self.tr("Amount Remaining to Pay:"), self.amount_due_label)
        form_layout.addRow(self.tr("Amount Received:"), self.amount_paid_spinbox)
        form_layout.addRow(self.tr("Payment Method:"), self.payment_method_combo)
        form_layout.addRow(self.tr("Transaction Reference (Optional):"), self.transaction_ref_edit)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText(self.tr("Record Payment"))
        self.button_box.button(QDialogButtonBox.Ok).setObjectName("recordPaymentButton") # For specific styling
        self.button_box.button(QDialogButtonBox.Cancel).setObjectName("cancelPaymentButton")
        self.button_box.accepted.connect(self._process_payment)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _load_payment_details(self):
        if not restaurant_paiement_crud or not self.commande:
            self.amount_due_label.setText(self.tr("Error loading payment details."))
            self.amount_paid_spinbox.setValue(0)
            return

        try:
            existing_payments = restaurant_paiement_crud.get_paiements_for_commande(self.commande.id)
            total_already_paid = sum(p.montant_paye for p in existing_payments)

            amount_due = (self.commande.total_commande_ttc or 0.0) - total_already_paid
            amount_due = max(0, amount_due) # Cannot be less than 0

            self.amount_due_label.setText(f"<b>{amount_due:.2f} €</b>")

            # Pre-fill amount_paid_spinbox with the remaining amount due
            self.amount_paid_spinbox.setValue(amount_due)

            if amount_due == 0 and self.commande.statut == 'payee':
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                self.amount_paid_spinbox.setEnabled(False)
                self.payment_method_combo.setEnabled(False)
                QMessageBox.information(self, self.tr("Order Paid"), self.tr("This order is already fully paid."))
            else:
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                self.amount_paid_spinbox.setEnabled(True)
                self.payment_method_combo.setEnabled(True)

        except Exception as e:
            logging.error(f"Error loading payment details for commande {self.commande.id}: {e}", exc_info=True)
            self.amount_due_label.setText(self.tr("Error."))
            self.amount_paid_spinbox.setValue(0)


    def _process_payment(self):
        if not restaurant_paiement_crud:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Payment CRUD operations not available."))
            return

        amount_received = self.amount_paid_spinbox.value()
        payment_method = self.payment_method_combo.currentText()
        transaction_ref = self.transaction_ref_edit.text().strip() or None

        if amount_received <= 0:
            QMessageBox.warning(self, self.tr("Invalid Amount"), self.tr("Payment amount must be positive."))
            return

        # Optional: Check if amount_received exceeds amount_due and ask for confirmation or handle change.
        # current_amount_due = float(self.amount_due_label.text().split(' ')[0].replace('<b>','').replace('</b>',''))
        # if amount_received > current_amount_due:
        #     reply = QMessageBox.question(self, self.tr("Overpayment"),
        #                                  self.tr("Amount received ({0:.2f}€) is greater than amount due ({1:.2f}€). Proceed and give change?").format(amount_received, current_amount_due),
        #                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        #     if reply == QMessageBox.No:
        #         return

        payment_data = {
            "montant_paye": amount_received,
            "methode_paiement": payment_method,
            "reference_transaction": transaction_ref
        }

        try:
            added_payment = restaurant_paiement_crud.add_paiement_to_commande(self.commande.id, payment_data)
            if added_payment:
                QMessageBox.information(self, self.tr("Payment Successful"),
                                        self.tr("Payment of {0:.2f}€ recorded successfully.").format(amount_received))

                # Refresh the commande object from DB to get updated status and totals
                # self.commande = restaurant_commande_crud.get_commande_by_id(self.commande.id)
                # self._load_payment_details() # Update display of amount due

                self.payment_processed_signal.emit(self.commande.id)
                self.accept() # Close the dialog
            else:
                QMessageBox.critical(self, self.tr("Payment Failed"), self.tr("Failed to record payment."))
        except ValueError as ve: # e.g., from CRUD if trying to pay for cancelled order
            QMessageBox.warning(self, self.tr("Payment Error"), str(ve))
        except Exception as e:
            logging.error(f"Error processing payment for commande {self.commande.id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Payment Error"), str(e))


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    logging.basicConfig(level=logging.INFO)

    # Dummy DB setup for standalone test
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    # Assuming models.py is in the parent directory relative to this ui/payment_dialog.py
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from models import Base as RestaurantBase, RestaurantTable as TestRestaurantTable, RestaurantCommande as TestRestaurantCommande, RestaurantPaiement as TestRestaurantPaiement

    engine = create_engine("sqlite:///:memory:")
    RestaurantBase.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def dummy_manage_conn_payment_test(func):
        def wrapper(*args, **kwargs):
            session = TestingSessionLocal()
            kwargs['conn'] = session
            try:
                result = func(*args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        return wrapper

    # Monkey-patch CRUDs for testing
    if restaurant_commande_crud and restaurant_paiement_crud:
        import cruds # Assuming cruds.py is in the parent directory
        cruds._manage_conn = dummy_manage_conn_payment_test
        # Patch specific CRUD instances if they don't use the module-level _manage_conn directly
        # For instance, if RestaurantPaiementCRUD overrides it or uses a different one.
        # However, the current structure suggests they use the imported _manage_conn.


        # Populate with a test table and a test commande
        session = TestingSessionLocal()
        try:
            test_table = session.query(TestRestaurantTable).first()
            if not test_table:
                test_table = TestRestaurantTable(numero_table="PayTest T1", capacite=2, statut="occupee")
                session.add(test_table)
                session.flush()

            test_commande = session.query(TestRestaurantCommande).filter_by(table_id=test_table.id, statut="en_cours").first()
            if not test_commande:
                commande_data_for_test = {
                    "table_id": test_table.id,
                    "statut": "en_cours",
                    "total_commande_ht": 50.0,
                    "total_commande_ttc": 60.0 # Example total
                }
                # Use CRUD, which should now use the dummy_manage_conn for this test context
                test_commande = cruds.restaurant_commande_crud.create_commande(commande_data_for_test, conn=session) # Pass session

            session.commit() # Ensure commande is committed before dialog uses it

            if test_commande:
                # Fetch it again to ensure all relationships (like .table) are loaded if needed by dialog
                # The get_commande_by_id in CRUD is designed to load relationships.
                full_test_commande = cruds.restaurant_commande_crud.get_commande_by_id(test_commande.id, conn=session)

                app = QApplication(sys.argv)
                dialog = PaymentDialog(commande=full_test_commande)

                def on_payment_processed(cid):
                    logging.info(f"Standalone Test: Payment processed for commande ID: {cid}. Dialog should close.")
                    # In a real app, this would trigger further UI updates.

                dialog.payment_processed_signal.connect(on_payment_processed)
                dialog.show()
                sys.exit(app.exec_())
            else:
                logging.error("Standalone Test: Failed to create or retrieve test commande for PaymentDialog.")

        except Exception as e:
            logging.error(f"Error in standalone test setup for PaymentDialog: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()
    else:
        logging.error("Standalone Test: CRUDS not available, cannot run PaymentDialog test.")
