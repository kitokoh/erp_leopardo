# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QGroupBox, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QEvent
from datetime import datetime
import db as db_manager # Assuming db_manager is accessible for saving notes

class NotesSection(QWidget):
    def __init__(self, client_info, notification_manager, current_user_id, parent_main_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.notification_manager = notification_manager
        self.current_user_id = current_user_id
        self.parent_main_widget = parent_main_widget # Reference to ClientMainWidget

        self._setup_ui()
        # Connect signals relevant to this section
        if hasattr(self, 'notes_edit'):
            self.notes_edit.installEventFilter(self)
            # Auto-save on textChanged might be too frequent, FocusOut is handled by eventFilter
            # self.notes_edit.textChanged.connect(self.save_client_notes_debounced) # Example for debouncing

    def _setup_ui(self):
        section_layout = QVBoxLayout(self)
        section_layout.setContentsMargins(0,0,0,0) # No margins for the widget itself if it's added to a groupbox

        self.notes_group_box = QGroupBox(self.tr("Notes"))
        self.notes_group_box.setCheckable(True)
        notes_group_layout = QVBoxLayout(self.notes_group_box)

        self.notes_container_widget = QWidget() # Container for notes_edit if groupbox is collapsed
        notes_container_layout = QVBoxLayout(self.notes_container_widget)
        notes_container_layout.setContentsMargins(0, 5, 0, 0)

        self.notes_edit = QTextEdit(self.client_info.get("notes", ""))
        self.notes_edit.setPlaceholderText(self.tr("Ajoutez des notes sur ce client..."))
        notes_container_layout.addWidget(self.notes_edit)

        notes_group_layout.addWidget(self.notes_container_widget)
        self.notes_group_box.setChecked(False) # Default to collapsed

        # Make the group box's content visibility tied to its checked state
        self.notes_group_box.toggled.connect(self.notes_container_widget.setVisible)
        self.notes_container_widget.setVisible(self.notes_group_box.isChecked())


        section_layout.addWidget(self.notes_group_box)

    def get_notes_text(self):
        return self.notes_edit.toPlainText()

    def set_notes_text(self, text):
        self.notes_edit.setText(text)

    def set_notes_read_only(self, read_only):
        self.notes_edit.setReadOnly(read_only)

    def save_client_notes(self):
        notes = self.notes_edit.toPlainText()
        client_id_to_update = self.client_info.get("client_id")

        if client_id_to_update is None:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible, impossible de sauvegarder les notes."))
            return False

        try:
            if db_manager.update_client(client_id_to_update, {'notes': notes}):
                self.client_info["notes"] = notes # Update local copy in this section
                # Notify parent if necessary, or parent reads directly
                if hasattr(self.parent_main_widget, 'client_info'): # Update parent's client_info too
                    self.parent_main_widget.client_info['notes'] = notes
                logging.info(f"Notes saved for client {client_id_to_update}")
                return True
            else:
                if self.notification_manager:
                    self.notification_manager.show(title=self.tr("Erreur Notes"), message=self.tr("Échec de la sauvegarde des notes."), type='ERROR')
                return False
        except Exception as e:
            if self.notification_manager:
                self.notification_manager.show(title=self.tr("Erreur Notes"), message=self.tr("Erreur de sauvegarde des notes: {0}").format(str(e)), type='ERROR')
            return False

    def eventFilter(self, obj, event):
        if obj is self.notes_edit:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    if event.modifiers() == Qt.ShiftModifier:
                        return super().eventFilter(obj, event)
                    else:
                        self.append_new_note_with_timestamp()
                        return True
            elif event.type() == QEvent.FocusOut:
                self.save_client_notes()
                return False
        return super().eventFilter(obj, event)

    def append_new_note_with_timestamp(self):
        cursor = self.notes_edit.textCursor()
        current_block = cursor.block()
        current_block_text_stripped = current_block.text().strip()
        is_already_timestamped = False
        text_after_timestamp = current_block_text_stripped

        if current_block_text_stripped.startswith("[") and "]" in current_block_text_stripped:
            try:
                potential_ts_part = current_block_text_stripped.split("]", 1)[0] + "]"
                datetime.strptime(potential_ts_part, "[%Y-%m-%d %H:%M:%S]")
                is_already_timestamped = True
                text_after_timestamp = current_block_text_stripped.split("]", 1)[1].strip()
            except ValueError:
                is_already_timestamped = False

        timestamp_prefix = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

        if not is_already_timestamped and current_block_text_stripped:
            new_content_for_current_line = f"{timestamp_prefix} {current_block_text_stripped}"
            cursor.beginEditBlock()
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertText(new_content_for_current_line)
            cursor.endEditBlock()
            cursor.movePosition(QTextCursor.EndOfBlock)
            self.notes_edit.setTextCursor(cursor)
            self.notes_edit.insertPlainText("\n" + f"{timestamp_prefix} ")
        elif is_already_timestamped and text_after_timestamp:
            cursor.movePosition(QTextCursor.EndOfBlock)
            self.notes_edit.setTextCursor(cursor)
            self.notes_edit.insertPlainText("\n" + f"{timestamp_prefix} ")
        elif not current_block_text_stripped:
            cursor.beginEditBlock()
            cursor.movePosition(QTextCursor.StartOfBlock)
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.insertText(f"{timestamp_prefix} ")
            cursor.endEditBlock()
            self.notes_edit.setTextCursor(cursor)
        else:
            cursor.movePosition(QTextCursor.EndOfBlock)
            self.notes_edit.setTextCursor(cursor)
            self.notes_edit.insertPlainText("\n" + f"{timestamp_prefix} ")

        self.save_client_notes() # Save after modification

    def tr(self, text, disambiguation=None, n=-1):
        # Delegate translation to the main widget or application
        if hasattr(self.parent_main_widget, 'tr'):
            return self.parent_main_widget.tr(text, disambiguation, n)
        return QApplication.translate("NotesSection", text, disambiguation, n)

    def get_group_box(self):
        """Returns the QGroupBox managed by this section."""
        return self.notes_group_box

    def is_checked(self):
        return self.notes_group_box.isChecked()

    def set_checked(self, checked):
        self.notes_group_box.setChecked(checked)

    def block_signals_group_box(self, block):
        self.notes_group_box.blockSignals(block)

    def set_container_visible(self, visible):
        self.notes_container_widget.setVisible(visible)
