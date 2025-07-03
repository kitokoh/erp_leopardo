# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QMessageBox, QCheckBox, QScrollArea, QWidget, QLabel
)
import logging

logger = logging.getLogger(__name__)

class ContactDialog(QDialog):
    def __init__(self, contact_data=None, link_data=None, manage_link_fields=False, parent=None):
        super().__init__(parent)
        self.contact_data_initial = contact_data if contact_data else {}
        self.link_data_initial = link_data if link_data else {}
        self.manage_link_fields = manage_link_fields # Determines if link-specific fields are shown

        self.setWindowTitle(self.tr("Ajouter/Modifier Contact") + (self.tr(" et Lien") if manage_link_fields else ""))
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)
        form_layout.setSpacing(10)

        # Contact Fields (from Contacts table)
        self.display_name_input = QLineEdit()
        form_layout.addRow(self.tr("Nom affiché*:"), self.display_name_input)

        self.given_name_input = QLineEdit()
        form_layout.addRow(self.tr("Prénom:"), self.given_name_input)

        self.family_name_input = QLineEdit()
        form_layout.addRow(self.tr("Nom de famille:"), self.family_name_input)

        self.email_input = QLineEdit()
        form_layout.addRow(self.tr("Email:"), self.email_input)

        self.phone_input = QLineEdit()
        form_layout.addRow(self.tr("Téléphone:"), self.phone_input)

        self.position_input = QLineEdit() # Job title / position
        form_layout.addRow(self.tr("Poste/Fonction:"), self.position_input)

        self.company_name_input = QLineEdit() # Contact's own company, if different from the entity
        form_layout.addRow(self.tr("Entreprise du contact:"), self.company_name_input)

        self.employee_status_combo = QComboBox()
        self.employee_status_combo.addItems([self.tr("N/A"), self.tr("Interne"), self.tr("Externe")])
        form_layout.addRow(self.tr("Statut employé:"), self.employee_status_combo)

        self.notes_input = QTextEdit() # General notes about the contact
        self.notes_input.setFixedHeight(80)
        form_layout.addRow(self.tr("Notes (Contact):"), self.notes_input)

        # Optional advanced fields (could be in a collapsible group)
        self.show_advanced_checkbox = QCheckBox(self.tr("Afficher les champs avancés"))
        self.show_advanced_checkbox.setChecked(False)
        form_layout.addRow(self.show_advanced_checkbox)

        self.advanced_fields_widgets = []

        self.phone_type_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Type téléphone:"), self.phone_type_input)

        self.email_type_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Type email:"), self.email_type_input)

        self.address_street_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Rue:"), self.address_street_input)

        self.address_city_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Ville:"), self.address_city_input)

        self.address_region_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Région/État:"), self.address_region_input)

        self.address_postalcode_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Code Postal:"), self.address_postalcode_input)

        self.address_country_input = QLineEdit()
        self._add_advanced_field(form_layout, self.tr("Pays:"), self.address_country_input)

        self.organization_name_input = QLineEdit() # For Google Contacts sync primarily
        self._add_advanced_field(form_layout, self.tr("Nom Organisation (Sync):"), self.organization_name_input)

        self.organization_title_input = QLineEdit() # For Google Contacts sync
        self._add_advanced_field(form_layout, self.tr("Titre Organisation (Sync):"), self.organization_title_input)

        self.birthday_input = QLineEdit() # Format YYYY-MM-DD
        self._add_advanced_field(form_layout, self.tr("Anniversaire (YYYY-MM-DD):"), self.birthday_input)

        self.show_advanced_checkbox.stateChanged.connect(self.toggle_advanced_fields_visibility)

        # Link-specific fields (from EntityContacts table)
        if self.manage_link_fields:
            self.link_fields_widgets = []

            separator = QWidget() # Simple separator
            separator.setMinimumHeight(1)
            separator.setStyleSheet("background-color: #c0c0c0;")
            form_layout.addRow(separator)

            link_header_label = QLabel(self.tr("Détails du Lien avec l'Entité"))
            link_header_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            form_layout.addRow(link_header_label)

            self.role_in_entity_input = QLineEdit()
            form_layout.addRow(self.tr("Rôle pour l'entité:"), self.role_in_entity_input)
            self.link_fields_widgets.extend([form_layout.labelForField(self.role_in_entity_input), self.role_in_entity_input])

            self.is_primary_checkbox = QCheckBox(self.tr("Contact principal pour cette entité"))
            form_layout.addRow(self.is_primary_checkbox)
            self.link_fields_widgets.append(self.is_primary_checkbox) # No label, checkbox is self-descriptive

            self.can_receive_docs_checkbox = QCheckBox(self.tr("Peut recevoir des documents pour cette entité"))
            form_layout.addRow(self.can_receive_docs_checkbox)
            self.link_fields_widgets.append(self.can_receive_docs_checkbox)

            self.link_notes_input = QTextEdit()
            self.link_notes_input.setFixedHeight(60)
            form_layout.addRow(self.tr("Notes (Lien):"), self.link_notes_input)
            self.link_fields_widgets.extend([form_layout.labelForField(self.link_notes_input), self.link_notes_input])

        scroll_widget.setLayout(form_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)
        self.toggle_advanced_fields_visibility() # Set initial state

    def _add_advanced_field(self, layout, label_text, widget):
        label = QLabel(label_text)
        layout.addRow(label, widget)
        self.advanced_fields_widgets.extend([label, widget])

    def toggle_advanced_fields_visibility(self):
        visible = self.show_advanced_checkbox.isChecked()
        for widget in self.advanced_fields_widgets:
            widget.setVisible(visible)

    def load_initial_data(self):
        # Load contact data
        self.display_name_input.setText(self.contact_data_initial.get('displayName', self.contact_data_initial.get('name', '')))
        self.given_name_input.setText(self.contact_data_initial.get('givenName', ''))
        self.family_name_input.setText(self.contact_data_initial.get('familyName', ''))
        self.email_input.setText(self.contact_data_initial.get('email', ''))
        self.phone_input.setText(self.contact_data_initial.get('phone', ''))
        self.position_input.setText(self.contact_data_initial.get('position', ''))
        self.company_name_input.setText(self.contact_data_initial.get('company_name', ''))
        self.notes_input.setPlainText(self.contact_data_initial.get('notes', ''))

        emp_status = self.contact_data_initial.get('employee_status', 'N/A').lower()
        if emp_status == 'internal':
            self.employee_status_combo.setCurrentIndex(1)
        elif emp_status == 'external':
            self.employee_status_combo.setCurrentIndex(2)
        else:
            self.employee_status_combo.setCurrentIndex(0) # N/A

        # Load advanced contact data
        self.phone_type_input.setText(self.contact_data_initial.get('phone_type', ''))
        self.email_type_input.setText(self.contact_data_initial.get('email_type', ''))
        self.address_street_input.setText(self.contact_data_initial.get('address_streetAddress', ''))
        self.address_city_input.setText(self.contact_data_initial.get('address_city', ''))
        self.address_region_input.setText(self.contact_data_initial.get('address_region', ''))
        self.address_postalcode_input.setText(self.contact_data_initial.get('address_postalCode', ''))
        self.address_country_input.setText(self.contact_data_initial.get('address_country', ''))
        self.organization_name_input.setText(self.contact_data_initial.get('organization_name', ''))
        self.organization_title_input.setText(self.contact_data_initial.get('organization_title', ''))
        self.birthday_input.setText(self.contact_data_initial.get('birthday_date', ''))

        # Load link-specific data if applicable
        if self.manage_link_fields:
            self.role_in_entity_input.setText(self.link_data_initial.get('role_in_entity', ''))
            self.is_primary_checkbox.setChecked(bool(self.link_data_initial.get('is_primary', False)))
            self.can_receive_docs_checkbox.setChecked(bool(self.link_data_initial.get('can_receive_documents', True)))
            self.link_notes_input.setPlainText(self.link_data_initial.get('link_notes', self.link_data_initial.get('notes',''))) # backward compatibility for 'notes' in link

    def get_contact_data(self) -> dict:
        emp_status_text = self.employee_status_combo.currentText()
        employee_status_value = "not_applicable"
        if emp_status_text == self.tr("Interne"):
            employee_status_value = "internal"
        elif emp_status_text == self.tr("Externe"):
            employee_status_value = "external"

        data = {
            "displayName": self.display_name_input.text().strip(),
            "givenName": self.given_name_input.text().strip(),
            "familyName": self.family_name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "position": self.position_input.text().strip(),
            "company_name": self.company_name_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "employee_status": employee_status_value,

            "phone_type": self.phone_type_input.text().strip(),
            "email_type": self.email_type_input.text().strip(),
            "address_streetAddress": self.address_street_input.text().strip(),
            "address_city": self.address_city_input.text().strip(),
            "address_region": self.address_region_input.text().strip(),
            "address_postalCode": self.address_postalcode_input.text().strip(),
            "address_country": self.address_country_input.text().strip(),
            "organization_name": self.organization_name_input.text().strip(),
            "organization_title": self.organization_title_input.text().strip(),
            "birthday_date": self.birthday_input.text().strip(),
        }
        # 'name' is often used as a fallback or primary identifier in some CRUDs.
        # Ensure it's populated, preferably from displayName or a combination.
        data['name'] = data['displayName'] if data['displayName'] else f"{data['givenName']} {data['familyName']}".strip()
        if not data['name']: # If still no name, it's an issue for some CRUDs
            pass # Validation will catch this
        return data

    def get_link_data(self) -> dict | None:
        if not self.manage_link_fields:
            return None
        return {
            "role_in_entity": self.role_in_entity_input.text().strip(),
            "is_primary": self.is_primary_checkbox.isChecked(),
            "can_receive_documents": self.can_receive_docs_checkbox.isChecked(),
            "notes": self.link_notes_input.toPlainText().strip() # notes for the link
        }

    def on_accept(self):
        contact_data = self.get_contact_data()
        if not contact_data.get('displayName') and not (contact_data.get('givenName') and contact_data.get('familyName')):
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le nom affiché ou Prénom/Nom de famille est requis."))
            self.display_name_input.setFocus()
            return

        # Potentially more validation here (e.g., email format, phone format)

        super().accept() # Emits the accepted signal

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    # Test 1: New contact, no link fields
    dialog1 = ContactDialog(manage_link_fields=False)
    if dialog1.exec_() == QDialog.Accepted:
        print("Dialog 1 (New Contact) Accepted. Data:")
        print("Contact Data:", dialog1.get_contact_data())
        print("Link Data:", dialog1.get_link_data())

    # Test 2: Edit contact, with link fields
    sample_contact = {
        'displayName': 'John Doe Test', 'email': 'john.test@example.com',
        'phone': '1234567890', 'employee_status': 'internal'
    }
    sample_link = {
        'role_in_entity': 'Test Role', 'is_primary': True, 'notes': 'Link specific notes here'
    }
    dialog2 = ContactDialog(contact_data=sample_contact, link_data=sample_link, manage_link_fields=True)
    if dialog2.exec_() == QDialog.Accepted:
        print("\nDialog 2 (Edit Contact & Link) Accepted. Data:")
        print("Contact Data:", dialog2.get_contact_data())
        print("Link Data:", dialog2.get_link_data())

    sys.exit(app.exec_())
