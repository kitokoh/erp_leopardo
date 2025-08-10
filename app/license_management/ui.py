# license_management/ui.py
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QApplication, QDialogButtonBox, QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from datetime import datetime # Import datetime

# Imports pour la logique métier et la connexion DB
from . import manager as license_manager
from db.connection import get_db_connection

# Import pour la configuration de l'URL du serveur
try:
    from config import LICENSE_REQUEST_SERVER_URL
except ImportError:
    LICENSE_REQUEST_SERVER_URL = "http://127.0.0.1:5678/api/license/request" # Fallback
    logging.warning("LICENSE_REQUEST_SERVER_URL non trouvée dans config.py, utilisation d'une URL par défaut.")

# Import pour les requêtes HTTP (sera utilisé dans _handle_request_new_license)
try:
    import requests
except ImportError:
    requests = None # Sera vérifié avant utilisation
    logging.error("La bibliothèque 'requests' n'est pas installée. La demande de nouvelle licence échouera.")


logger = logging.getLogger(__name__)

class LicenseDialog(QDialog):
    license_activated_successfully = pyqtSignal()

    def __init__(self, current_user_info: dict, initial_license_info: dict | None = None, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.current_license_info = initial_license_info

        if self.current_license_info is None and self.current_user_info:
            self._load_current_license_info()

        self.setWindowTitle(self.tr("Gestion de la Licence"))
        self.setWindowIcon(QIcon(":/icons/settings.svg"))
        self.setMinimumWidth(500)
        self.setModal(True)

        self._init_ui()
        self._update_display()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        status_group = QGroupBox(self.tr("Statut de votre Licence Actuelle"))
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel(self.tr("Chargement..."))
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(status_group)

        activation_group = QGroupBox(self.tr("Activer une Nouvelle Licence"))
        activation_form_layout = QFormLayout(activation_group)

        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText(self.tr("Entrez votre clé de licence ici"))
        activation_form_layout.addRow(self.tr("Clé de Licence :"), self.license_key_input)

        self.activate_button = QPushButton(self.tr("Activer la Clé"))
        self.activate_button.setIcon(QIcon(":/icons/check.svg"))
        self.activate_button.clicked.connect(self._handle_activate_license)

        button_layout_activation = QHBoxLayout()
        button_layout_activation.addStretch()
        button_layout_activation.addWidget(self.activate_button)
        button_layout_activation.addStretch()
        activation_form_layout.addRow(button_layout_activation)

        main_layout.addWidget(activation_group)

        options_group = QGroupBox(self.tr("Autres Options"))
        options_layout = QVBoxLayout(options_group) # Changed to QVBoxLayout for vertical stacking

        # Layout pour la demande de nouvelle licence
        request_license_form_layout = QFormLayout() # Using QFormLayout for label-combo pair

        self.requested_license_type_combo = QComboBox()
        self.requested_license_type_combo.addItem(self.tr("Limitée"), "limite")
        self.requested_license_type_combo.addItem(self.tr("Complète"), "complet")
        request_license_form_layout.addRow(self.tr("Type de licence souhaité :"), self.requested_license_type_combo)

        self.request_new_license_button = QPushButton(self.tr("Passer la Demande de Nouvelle Licence"))
        self.request_new_license_button.setIcon(QIcon(":/icons/help-circle.svg"))
        self.request_new_license_button.clicked.connect(self._handle_request_new_license)

        # Add the form layout and button to the options_layout
        options_layout.addLayout(request_license_form_layout) # Add the form layout

        # Center the "Passer la Demande" button
        request_button_layout = QHBoxLayout()
        request_button_layout.addStretch()
        request_button_layout.addWidget(self.request_new_license_button)
        request_button_layout.addStretch()
        options_layout.addLayout(request_button_layout) # Add the centered button layout

        options_layout.addSpacing(10) # Add some space

        self.try_free_button = QPushButton(self.tr("Essayer la Version Gratuite (30 jours)"))
        self.try_free_button.setIcon(QIcon(":/icons/unlock.svg"))
        self.try_free_button.clicked.connect(self._handle_try_free_license)
        options_layout.addWidget(self.try_free_button)

        main_layout.addWidget(options_group)

        self.button_box = QDialogButtonBox()
        self.ok_button = self.button_box.addButton(QDialogButtonBox.Ok)
        self.close_button = self.button_box.addButton(QDialogButtonBox.Close)
        self.ok_button.setText(self.tr("Continuer"))
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        self.close_button.clicked.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _load_current_license_info(self):
        if not self.current_user_info or not self.current_user_info.get('user_id'):
            logger.warning("Impossible de charger les informations de licence: user_info manquant.")
            self.current_license_info = None
            return
        conn = None
        try:
            conn = get_db_connection()
            is_valid, _, lic_details = license_manager.check_license_validity(conn, self.current_user_info['user_id'])
            self.current_license_info = lic_details
            if is_valid:
                self.current_license_info = lic_details
        except Exception as e:
            logger.error(f"Erreur lors du chargement des informations de licence: {e}", exc_info=True)
            self.current_license_info = None
        finally:
            if conn:
                conn.close()

    def _update_display(self):
        self._load_current_license_info()
        if self.current_license_info and self.current_license_info.get('is_active'):
            display_text = license_manager.get_current_license_display_info(get_db_connection(), self.current_user_info['user_id'])
            self.status_label.setText(self.tr("<b>Statut :</b> Valide\n") + display_text)
            self.status_label.setStyleSheet("color: green;")
            self.ok_button.setEnabled(True)
            self.activate_button.setText(self.tr("Activer une Autre Clé"))
            self.try_free_button.setEnabled(False)
            self.try_free_button.setToolTip(self.tr("Vous avez déjà une licence active."))
        elif self.current_license_info and not self.current_license_info.get('is_active'):
            reason = self.tr("Votre licence actuelle n'est plus active.")
            if self.current_license_info.get('expiration_date'):
                try:
                    exp_dt = datetime.fromisoformat(self.current_license_info['expiration_date'])
                    if exp_dt < datetime.now():
                        reason = self.tr("Votre licence de type '{0}' a expiré le {1}.") \
                                 .format(self.current_license_info.get('license_type', 'N/A').capitalize(),
                                         exp_dt.strftime('%d/%m/%Y'))
                except ValueError: pass
            self.status_label.setText(self.tr("<b>Statut :</b> Invalide\n") + reason)
            self.status_label.setStyleSheet("color: red;")
            self.ok_button.setEnabled(False)
            self.activate_button.setText(self.tr("Activer la Clé"))
            self._check_free_license_availability()
        else:
            self.status_label.setText(self.tr("<b>Statut :</b> Aucune licence active trouvée pour votre compte."))
            self.status_label.setStyleSheet("color: orange;")
            self.ok_button.setEnabled(False)
            self.activate_button.setText(self.tr("Activer la Clé"))
            self._check_free_license_availability()

    def _check_free_license_availability(self):
        conn = None
        can_try_free = True
        tooltip_message = self.tr("Activer une licence gratuite limitée à 30 jours.")
        if not self.current_user_info or not self.current_user_info.get('user_id'): # Vérification ajoutée
            can_try_free = False
            tooltip_message = self.tr("Informations utilisateur non disponibles.")
        else:
            try:
                conn = get_db_connection()
                machine_id = license_manager.get_machine_identifier()
                existing_free_on_machine = license_manager.cruds.get_licenses_by_machine_info(conn, machine_id, license_type="gratuit")
                if any(lic['user_id'] == self.current_user_info['user_id'] for lic in existing_free_on_machine):
                    can_try_free = False
                    tooltip_message = self.tr("Une licence gratuite a déjà été utilisée sur cette machine pour votre compte.")
                else:
                    user_lic = license_manager.cruds.get_license_by_user_id(conn, self.current_user_info['user_id'])
                    if user_lic and user_lic['license_type'] == "gratuit":
                        can_try_free = False
                        tooltip_message = self.tr("Une licence gratuite a déjà été associée à votre compte.")
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de la disponibilité de la licence gratuite: {e}", exc_info=True)
                can_try_free = False
                tooltip_message = self.tr("Erreur lors de la vérification de la disponibilité.")
            finally:
                if conn: conn.close()
        self.try_free_button.setEnabled(can_try_free)
        self.try_free_button.setToolTip(tooltip_message)

    def _handle_activate_license(self):
        license_key = self.license_key_input.text().strip()
        if not license_key:
            QMessageBox.warning(self, self.tr("Clé Manquante"), self.tr("Veuillez entrer une clé de licence."))
            return
        conn = None
        try:
            conn = get_db_connection()
            success, message = license_manager.activate_license(conn, self.current_user_info['user_id'], license_key)
            if success:
                QMessageBox.information(self, self.tr("Activation Réussie"), message)
                self.license_key_input.clear()
                self.license_activated_successfully.emit()
            else:
                QMessageBox.warning(self, self.tr("Échec d'Activation"), message)
        except Exception as e:
            logger.error(f"Erreur lors de l'activation de la clé {license_key}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur inattendue est survenue lors de l'activation."))
        finally:
            if conn: conn.close()
        self._update_display()

    def _handle_try_free_license(self):
        reply = QMessageBox.question(self, self.tr("Confirmation Licence Gratuite"),
                                     self.tr("Voulez-vous activer une licence gratuite de 30 jours ?\n"
                                             "Cette option n'est généralement disponible qu'une seule fois par machine/compte."),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No: return
        conn = None
        try:
            conn = get_db_connection()
            new_license_info, message = license_manager.activate_free_license(conn, self.current_user_info['user_id'])
            if new_license_info:
                QMessageBox.information(self, self.tr("Licence Gratuite Activée"), message)
                self.license_activated_successfully.emit()
            else:
                QMessageBox.warning(self, self.tr("Échec Licence Gratuite"), message)
        except Exception as e:
            logger.error(f"Erreur lors de l'activation de la licence gratuite: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur inattendue est survenue."))
        finally:
            if conn: conn.close()
        self._update_display()

    def _handle_request_new_license(self):
        if requests is None:
            QMessageBox.critical(self, self.tr("Erreur de Dépendance"),
                                 self.tr("La bibliothèque 'requests' est nécessaire pour cette fonctionnalité mais n'est pas installée."))
            return

        if not self.current_user_info or not self.current_user_info.get('user_id'):
            QMessageBox.warning(self, self.tr("Erreur Utilisateur"),
                                self.tr("Impossible d'identifier l'utilisateur actuel pour la demande de licence."))
            return

        requested_type = self.requested_license_type_combo.currentData() # 'limite' ou 'complet'

        payload = {
            "user_id": self.current_user_info.get('user_id'),
            "username": self.current_user_info.get('username'),
            "email": self.current_user_info.get('email'), # Assurez-vous que l'email est dans current_user_info
            "current_license_type": self.current_license_info.get('license_type') if self.current_license_info else None,
            "current_license_key": self.current_license_info.get('license_key') if self.current_license_info else None,
            "current_expiration_date": self.current_license_info.get('expiration_date') if self.current_license_info else None,
            "requested_license_type": requested_type,
            "machine_info": license_manager.get_machine_identifier(),
            "request_timestamp": datetime.now().isoformat()
        }

        # Nettoyer payload des valeurs None pour current_license_* si elles ne sont pas présentes
        for key in ["current_license_type", "current_license_key", "current_expiration_date"]:
            if payload[key] is None:
                del payload[key]


        if not payload.get("email"): # Vérification si l'email est disponible
            QMessageBox.warning(self, self.tr("Information Manquante"),
                                self.tr("L'adresse e-mail de l'utilisateur est nécessaire pour la demande de licence et n'a pas pu être récupérée."))
            logger.warning(f"Demande de licence pour {payload.get('username')}: email manquant dans current_user_info.")
            return

        try:
            self.request_new_license_button.setEnabled(False)
            self.request_new_license_button.setText(self.tr("Envoi en cours..."))
            QApplication.processEvents() # Permet à l'UI de se mettre à jour

            response = requests.post(LICENSE_REQUEST_SERVER_URL, json=payload, timeout=10) # Timeout de 10s
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP 4xx/5xx

            response_data = response.json()
            if response_data.get("status") == "success":
                QMessageBox.information(self, self.tr("Demande Envoyée"), response_data.get("message", self.tr("Votre demande a été envoyée avec succès.")))
            else:
                QMessageBox.warning(self, self.tr("Erreur de Demande"), response_data.get("message", self.tr("Le serveur a retourné une erreur.")))

        except requests.exceptions.Timeout:
            logger.error(f"Timeout lors de la demande de licence à {LICENSE_REQUEST_SERVER_URL}")
            QMessageBox.critical(self, self.tr("Erreur Réseau"), self.tr("La demande a expiré (timeout). Veuillez vérifier votre connexion internet ou réessayer plus tard."))
        except requests.exceptions.ConnectionError:
            logger.error(f"Erreur de connexion lors de la demande de licence à {LICENSE_REQUEST_SERVER_URL}")
            QMessageBox.critical(self, self.tr("Erreur Réseau"), self.tr("Impossible de se connecter au serveur de licences. Veuillez vérifier votre connexion internet ou l'URL du serveur."))
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP {e.response.status_code} lors de la demande de licence: {e.response.text}")
            try:
                err_data = e.response.json()
                msg = err_data.get("message", e.response.text)
            except ValueError: # Non-JSON response
                msg = e.response.text
            QMessageBox.critical(self, self.tr("Erreur Serveur"), self.tr("Le serveur a retourné une erreur {0} : {1}").format(e.response.status_code, msg))
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la demande de nouvelle licence: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur inattendue est survenue : {0}").format(str(e)))
        finally:
            self.request_new_license_button.setEnabled(True)
            self.request_new_license_button.setText(self.tr("Passer la Demande de Nouvelle Licence"))


    def accept(self):
        self._load_current_license_info()
        if self.current_license_info and self.current_license_info.get('is_active'):
            logger.info("LicenseDialog acceptée avec une licence valide.")
            super().accept()
        else:
            logger.warning("Tentative d'accepter LicenseDialog sans licence valide.")
            QMessageBox.warning(self, self.tr("Licence Invalide"),
                                self.tr("Vous devez avoir une licence valide pour continuer."))

    def get_current_valid_license_info(self) -> dict | None:
        if self.current_license_info and self.current_license_info.get('is_active'):
            return self.current_license_info
        return None

# Code de test (if __name__ == '__main__') omis pour la concision, mais était présent dans la version précédente.
# Il faudrait le remettre si on veut tester ce fichier directement.
# Il nécessiterait de s'assurer que la DB est accessible et qu'un utilisateur existe.
# Pour le test de _handle_request_new_license, il faudrait aussi lancer license_request_server.py.

# Exemple de bloc de test (à adapter et à placer à la fin du fichier si besoin)
if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    app = QApplication(sys.argv)

    # Créer un utilisateur factice pour le test
    # Note: Pour que les cruds fonctionnent, une vraie DB initialisée est nécessaire.
    # Ce test est plus pour l'UI elle-même et le flux de base.
    # Assurez-vous que config.DATABASE_PATH pointe vers une DB valide et initialisée.

    test_user = None
    conn_test_ui = None
    try:
        from db.cruds import users_crud # Assurez-vous que ce chemin est correct
        conn_test_ui = get_db_connection()
        all_users = users_crud.get_all_users(conn_test_ui, limit=1)
        if all_users:
            test_user = all_users[0]
            logger.info(f"UI Test: Utilisateur de test chargé: {test_user.get('username')}")
        else:
            logger.warning("UI Test: Aucun utilisateur trouvé. Utilisation de données placeholder.")
            test_user = {"user_id": "ui_test_user", "username": "uitest", "email": "ui@test.com", "role_name": "user"}
    except Exception as e:
        logger.error(f"UI Test: Erreur DB - {e}. Utilisation de données placeholder.")
        test_user = {"user_id": "ui_test_user", "username": "uitest", "email": "ui@test.com", "role_name": "user"}
    finally:
        if conn_test_ui:
            conn_test_ui.close()

    if test_user:
        # Pour tester la demande de licence, assurez-vous que license_request_server.py est lancé.
        # python license_request_server.py
        # Puis exécutez ce fichier de test.

        dialog = LicenseDialog(current_user_info=test_user)
        dialog.exec_()
    else:
        logger.error("UI Test: Impossible de lancer LicenseDialog sans informations utilisateur.")

    sys.exit(app.exec_())
