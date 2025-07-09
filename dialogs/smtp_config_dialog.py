# dialogs/smtp_config_dialog.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QDialogButtonBox, QMessageBox, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt
import db # Assuming db.__init__ exports the necessary smtp_configs_crud functions
import smtplib
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)

class SmtpConfigDialog(QDialog):
    def __init__(self, config_id: int | None = None, parent=None):
        super().__init__(parent)
        self.config_id = config_id
        self.is_edit_mode = self.config_id is not None
        self.original_data = None

        self.setWindowTitle(self.tr("Modifier la Configuration SMTP") if self.is_edit_mode else self.tr("Ajouter une Configuration SMTP"))
        self.setMinimumWidth(450)

        self._setup_ui()
        if self.is_edit_mode:
            self._load_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow) # Ensure fields expand

        self.config_name_edit = QLineEdit()
        self.config_name_edit.setPlaceholderText(self.tr("Ex: Mon Gmail Personnel, SMTP Entreprise"))
        form_layout.addRow(self.tr("Nom de la configuration:"), self.config_name_edit)

        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText(self.tr("Ex: smtp.gmail.com, mail.example.com"))
        form_layout.addRow(self.tr("Serveur SMTP:"), self.smtp_server_edit)

        self.smtp_port_spinbox = QSpinBox()
        self.smtp_port_spinbox.setRange(1, 65535)
        self.smtp_port_spinbox.setValue(587) # Common default for TLS
        form_layout.addRow(self.tr("Port SMTP:"), self.smtp_port_spinbox)

        self.sender_email_edit = QLineEdit()
        self.sender_email_edit.setPlaceholderText(self.tr("Ex: utilisateur@example.com"))
        form_layout.addRow(self.tr("Adresse email de l'expéditeur:"), self.sender_email_edit)

        self.sender_display_name_edit = QLineEdit()
        self.sender_display_name_edit.setPlaceholderText(self.tr("Ex: Support Technique, Votre Nom"))
        form_layout.addRow(self.tr("Nom d'affichage de l'expéditeur (Optionnel):"), self.sender_display_name_edit)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText(self.tr("Souvent identique à l'email de l'expéditeur"))
        form_layout.addRow(self.tr("Nom d'utilisateur SMTP:"), self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText(self.tr("Laissez vide si inchangé (en mode édition)"))
        form_layout.addRow(self.tr("Mot de passe SMTP:"), self.password_edit)

        self.use_tls_checkbox = QCheckBox(self.tr("Utiliser TLS/STARTTLS"))
        self.use_tls_checkbox.setChecked(True)
        # Add an empty label for alignment if needed, or just add the checkbox directly
        # form_layout.addRow("", self.use_tls_checkbox)
        # Adding directly to form_layout often works better for single checkboxes
        form_layout.addRow(self.use_tls_checkbox)


        main_layout.addLayout(form_layout)

        # Test connection button
        self.test_connection_button = QPushButton(self.tr("Tester la Connexion"))
        self.test_connection_button.setToolTip(self.tr("Tenter une connexion au serveur SMTP et envoyer un email de test."))
        self.test_connection_button.clicked.connect(self._test_smtp_connection)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.test_connection_button)
        buttons_layout.addStretch(1)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        buttons_layout.addWidget(self.button_box) # Add standard OK/Cancel to the right

        main_layout.addLayout(buttons_layout) # Add the QHBoxLayout with test button and buttonBox

    def _load_data(self):
        if not self.is_edit_mode or self.config_id is None:
            return

        try:
            self.original_data = db.get_smtp_config_by_id(self.config_id)
            if not self.original_data:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Configuration SMTP non trouvée."))
                self.reject() # Close dialog if data can't be loaded
                return

            self.config_name_edit.setText(self.original_data.get('config_name', ''))
            self.smtp_server_edit.setText(self.original_data.get('smtp_server', ''))
            self.smtp_port_spinbox.setValue(self.original_data.get('smtp_port', 587))
            self.sender_email_edit.setText(self.original_data.get('sender_email_address', ''))
            self.sender_display_name_edit.setText(self.original_data.get('sender_display_name', ''))
            self.username_edit.setText(self.original_data.get('username', ''))
            # Password is not pre-filled for security. User must re-enter if changing.
            # The placeholder "Laissez vide si inchangé" guides this.
            self.use_tls_checkbox.setChecked(bool(self.original_data.get('use_tls', True)))

        except Exception as e:
            logger.error(f"Error loading SMTP config ID {self.config_id} for editing: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur de chargement"),
                                 self.tr("Impossible de charger les détails de la configuration SMTP: {0}").format(str(e)))
            self.reject()

    def get_data(self) -> dict:
        """Returns the data from the dialog fields."""
        data = {
            'config_name': self.config_name_edit.text().strip(),
            'smtp_server': self.smtp_server_edit.text().strip(),
            'smtp_port': self.smtp_port_spinbox.value(),
            'sender_email_address': self.sender_email_edit.text().strip(),
            'sender_display_name': self.sender_display_name_edit.text().strip(),
            'username': self.username_edit.text().strip(),
            'use_tls': self.use_tls_checkbox.isChecked()
        }
        # Only include password if it's entered (for edit mode, means change; for add mode, always included)
        password_text = self.password_edit.text()
        if password_text: # If user typed something in the password field
            data['password'] = password_text
        elif not self.is_edit_mode: # In add mode, if password is empty, it's an empty password
             data['password'] = ''
        # If in edit mode and password_text is empty, 'password' key is not added,
        # so CRUD update won't change the password.
        return data

    def _validate_input(self, data: dict) -> bool:
        if not data['config_name']:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le nom de la configuration est requis."))
            self.config_name_edit.setFocus()
            return False
        if not data['smtp_server']:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("L'adresse du serveur SMTP est requise."))
            self.smtp_server_edit.setFocus()
            return False
        if not data['sender_email_address']:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("L'adresse email de l'expéditeur est requise."))
            self.sender_email_edit.setFocus()
            return False

        # In add mode, username and password might be required by some servers even if not strictly by all.
        # For simplicity, we'll allow them to be empty, but a real app might enforce them.
        # if not self.is_edit_mode and (not data.get('username') or not data.get('password')):
        #     QMessageBox.warning(self, self.tr("Champs Requis"), self.tr("Le nom d'utilisateur et le mot de passe SMTP sont généralement requis pour les nouvelles configurations."))
        #     # self.username_edit.setFocus() # or password_edit
        #     # return False

        # Check for duplicate config_name if adding, or if changed during edit
        existing_by_name = db.get_smtp_config_by_name(data['config_name'])
        if self.is_edit_mode:
            if existing_by_name and existing_by_name['smtp_config_id'] != self.config_id:
                QMessageBox.warning(self, self.tr("Nom Dupliqué"), self.tr("Une autre configuration SMTP avec ce nom existe déjà."))
                self.config_name_edit.setFocus()
                return False
        else: # Add mode
            if existing_by_name:
                QMessageBox.warning(self, self.tr("Nom Dupliqué"), self.tr("Une configuration SMTP avec ce nom existe déjà."))
                self.config_name_edit.setFocus()
                return False
        return True

    def _on_accept(self):
        data_to_save = self.get_data()
        if not self._validate_input(data_to_save):
            return

        try:
            if self.is_edit_mode:
                success = db.update_smtp_config(self.config_id, data_to_save)
                if success:
                    logger.info(f"SMTP configuration ID {self.config_id} updated.")
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Configuration SMTP mise à jour avec succès."))
                    self.accept()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de mettre à jour la configuration SMTP. Aucune ligne affectée ou erreur."))
            else: # Add mode
                new_id = db.add_smtp_config(data_to_save)
                if new_id:
                    logger.info(f"New SMTP configuration added with ID: {new_id}.")
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Nouvelle configuration SMTP ajoutée avec succès."))
                    self.config_id = new_id # Store new ID if needed by caller
                    self.accept()
                else:
                    QMessageBox.critical(self, self.tr("Échec"), self.tr("Impossible d'ajouter la nouvelle configuration SMTP."))
        except Exception as e:
            logger.error(f"Error saving SMTP configuration: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Sauvegarde"),
                                 self.tr("Une erreur est survenue lors de la sauvegarde: {0}").format(str(e)))

    def _test_smtp_connection(self):
        data = self.get_data()
        smtp_server = data['smtp_server']
        smtp_port = data['smtp_port']
        username = data.get('username', '')
        # For testing, we need the password if it's set or if it's an existing config
        password_to_test = data.get('password')
        if not password_to_test and self.is_edit_mode and self.original_data:
            # If password field is empty in edit mode, try to use original password for test
            # This is a simplification; a real app might require re-entry or have a secure way to re-use.
            # For now, we assume original_data holds the (potentially obfuscated) password.
            # If it's obfuscated, this test won't work without de-obfuscation.
            # The CRUD layer uses base64 for now, so we'd need to decode that.
            # Let's assume for now the test needs a plainly entered password or the stored one is plain for test purposes.
            # This part needs careful consideration for security if passwords are encrypted/hashed.
            # For this step, we'll assume password_edit must contain the password for testing.
            if not self.password_edit.text():
                 QMessageBox.warning(self, self.tr("Mot de passe requis"),
                                     self.tr("Veuillez entrer le mot de passe SMTP pour le test de connexion."))
                 self.password_edit.setFocus()
                 return
            password_to_test = self.password_edit.text()


        use_tls = data['use_tls']
        sender_email = data['sender_email_address']

        if not smtp_server or not smtp_port or not sender_email:
            QMessageBox.warning(self, self.tr("Informations Manquantes"),
                                self.tr("Serveur SMTP, port et email expéditeur sont requis pour le test."))
            return

        try:
            # Prompt for a recipient email for the test
            recipient_email, ok = QLineEdit.getText(self, self.tr("Email de Test"),
                                                    self.tr("Entrez l'adresse email destinataire pour le test :"),
                                                    QLineEdit.Normal, "")
            if not (ok and recipient_email and "@" in recipient_email):
                QMessageBox.information(self, self.tr("Test Annulé"), self.tr("Test de connexion annulé ou email destinataire invalide."))
                return

            msg = MIMEText(self.tr("Ceci est un email de test de la configuration SMTP."))
            msg['Subject'] = self.tr("Email de Test SMTP")
            msg['From'] = f"{data.get('sender_display_name', sender_email)} <{sender_email}>"
            msg['To'] = recipient_email

            self.setCursor(Qt.WaitCursor)
            QApplication.processEvents()


            if use_tls:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else: # SSL - less common now, usually on port 465
                # For SSL, smtplib.SMTP_SSL should be used.
                # We'll assume TLS if checked, plain if not. Port should guide SSL/TLS.
                # A more robust solution would have a "Security Type" dropdown (None, TLS, SSL).
                # For now, checkbox handles TLS, otherwise plain.
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.ehlo()


            if username and password_to_test:
                server.login(username, password_to_test)

            server.sendmail(sender_email, [recipient_email], msg.as_string())
            server.quit()

            self.unsetCursor()
            QMessageBox.information(self, self.tr("Test de Connexion Réussi"),
                                    self.tr("Connexion SMTP réussie et email de test envoyé à {0}.").format(recipient_email))
        except smtplib.SMTPAuthenticationError:
            self.unsetCursor()
            QMessageBox.critical(self, self.tr("Échec de l'Authentification"),
                                 self.tr("Authentification SMTP échouée. Vérifiez nom d'utilisateur et mot de passe."))
        except smtplib.SMTPConnectError:
            self.unsetCursor()
            QMessageBox.critical(self, self.tr("Échec de Connexion"),
                                 self.tr("Impossible de se connecter au serveur SMTP. Vérifiez l'adresse et le port."))
        except smtplib.SMTPServerDisconnected:
            self.unsetCursor()
            QMessageBox.critical(self, self.tr("Serveur Déconnecté"),
                                 self.tr("Le serveur SMTP s'est déconnecté de manière inattendue."))
        except smtplib.SMTPException as e:
            self.unsetCursor()
            logger.error(f"SMTP test connection error: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur SMTP"),
                                 self.tr("Une erreur SMTP est survenue : {0}").format(str(e)))
        except ConnectionRefusedError: # More specific network error
            self.unsetCursor()
            QMessageBox.critical(self, self.tr("Connexion Refusée"),
                                 self.tr("La connexion au serveur SMTP a été refusée. Le serveur est-il en ligne et le port correct?"))

        except Exception as e:
            self.unsetCursor()
            logger.error(f"Unexpected error during SMTP test connection: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"),
                                 self.tr("Une erreur inattendue est survenue : {0}").format(str(e)))
        finally:
            self.unsetCursor()


if __name__ == '__main__':
    # This part is for testing the dialog standalone.
    # It requires a QApplication instance and a way to manage DB connections for the CRUD calls.
    from PyQt5.QtWidgets import QApplication
    import sys
    import os

    # Minimal logging setup for test
    logging.basicConfig(level=logging.DEBUG)

    # --- Mocking _manage_conn for standalone SmtpConfigDialog testing ---
    import functools
    DB_PATH_DIALOG_TEST = 'test_smtp_dialog.db'

    if os.path.exists(DB_PATH_DIALOG_TEST):
        os.remove(DB_PATH_DIALOG_TEST)

    # Global mock connection for the test duration
    _test_conn_global = None

    def get_test_db_connection():
        global _test_conn_global
        if _test_conn_global is None or _test_conn_global.closed: # type: ignore
            _test_conn_global = sqlite3.connect(DB_PATH_DIALOG_TEST)
            _test_conn_global.executescript("""
            CREATE TABLE IF NOT EXISTS SmtpConfigs (
                smtp_config_id INTEGER PRIMARY KEY AUTOINCREMENT, config_name TEXT NOT NULL UNIQUE,
                smtp_server TEXT NOT NULL, smtp_port INTEGER NOT NULL, username TEXT,
                password_encrypted TEXT, use_tls BOOLEAN DEFAULT TRUE, is_default BOOLEAN DEFAULT FALSE,
                sender_email_address TEXT NOT NULL, sender_display_name TEXT
            );
            """)
            _test_conn_global.commit()
        return _test_conn_global

    # Mock the db module functions that SmtpConfigDialog uses
    # This assumes SmtpConfigDialog calls db.get_smtp_config_by_id etc. directly
    # We need to patch these at the 'db' module level as imported by the dialog.

    original_db_get_by_id = db.get_smtp_config_by_id
    original_db_get_by_name = db.get_smtp_config_by_name
    original_db_update = db.update_smtp_config
    original_db_add = db.add_smtp_config

    def mock_db_get_smtp_config_by_id(config_id):
        return db.cruds.smtp_configs_crud.get_smtp_config_by_id(config_id, conn=get_test_db_connection())
    def mock_db_get_smtp_config_by_name(name):
        return db.cruds.smtp_configs_crud.get_smtp_config_by_name(name, conn=get_test_db_connection())
    def mock_db_update_smtp_config(config_id, data):
        return db.cruds.smtp_configs_crud.update_smtp_config(config_id, data, conn=get_test_db_connection())
    def mock_db_add_smtp_config(data):
        return db.cruds.smtp_configs_crud.add_smtp_config(data, conn=get_test_db_connection())

    db.get_smtp_config_by_id = mock_db_get_smtp_config_by_id
    db.get_smtp_config_by_name = mock_db_get_smtp_config_by_name
    db.update_smtp_config = mock_db_update_smtp_config
    db.add_smtp_config = mock_db_add_smtp_config
    # --- End Mocking for SmtpConfigDialog ---


    app = QApplication(sys.argv)

    # Test 1: Add new config
    print("Testing ADD mode:")
    add_dialog = SmtpConfigDialog(parent=None)
    if add_dialog.exec_() == QDialog.Accepted:
        print("Add dialog accepted. Data:", add_dialog.get_data())
        print("New config ID (if add was successful):", add_dialog.config_id)
        added_id_for_edit_test = add_dialog.config_id
    else:
        print("Add dialog cancelled.")
        added_id_for_edit_test = None


    # Test 2: Edit existing config (if one was added)
    if added_id_for_edit_test:
        print(f"\nTesting EDIT mode for ID: {added_id_for_edit_test}")
        edit_dialog = SmtpConfigDialog(config_id=added_id_for_edit_test, parent=None)
        if edit_dialog.exec_() == QDialog.Accepted:
            print("Edit dialog accepted. Data:", edit_dialog.get_data())
        else:
            print("Edit dialog cancelled.")
    else:
        print("\nSkipping EDIT mode test as ADD mode did not result in a config ID.")

    # Clean up global mock connection and test DB
    if _test_conn_global:
        _test_conn_global.close()
    if os.path.exists(DB_PATH_DIALOG_TEST):
        os.remove(DB_PATH_DIALOG_TEST)
        print(f"\nCleaned up test database: {DB_PATH_DIALOG_TEST}")

    # Restore original db functions if they were patched
    db.get_smtp_config_by_id = original_db_get_by_id
    db.get_smtp_config_by_name = original_db_get_by_name
    db.update_smtp_config = original_db_update
    db.add_smtp_config = original_db_add

    # sys.exit(app.exec_()) # Don't run app loop if just testing dialog creation/logic
    print("SmtpConfigDialog standalone test completed.")
