from sqlalchemy.orm import Session
from app.models.db.settings.applicationsettings import Applicationsettings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SettingsCRUD:
    def get_setting(self, db: Session, key: str, default: any = None) -> any:
        setting = db.query(Applicationsettings).filter(Applicationsettings.setting_key == key).first()
        if setting:
            return setting.setting_value
        return default

    def set_setting(self, db: Session, key: str, value: str) -> bool:
        try:
            setting = db.query(Applicationsettings).filter(Applicationsettings.setting_key == key).first()
            if setting:
                setting.setting_value = value
            else:
                setting = Applicationsettings(setting_key=key, setting_value=value)
                db.add(setting)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to set setting for key {key}, value {value}: {e}", exc_info=True)
            db.rollback()
            return False

    def get_next_invoice_number(self, db: Session) -> str:
        current_year = datetime.now().year
        setting_key = f"last_invoice_sequence_{current_year}"
        prefix = f"INV-{current_year}-"

        last_sequence_str = self.get_setting(db, setting_key)

        last_sequence = 0
        if last_sequence_str:
            try:
                last_sequence = int(last_sequence_str)
            except ValueError:
                logger.warning(f"Invalid invoice sequence number '{last_sequence_str}' in settings for key '{setting_key}'. Resetting to 0.")
                last_sequence = 0

        next_sequence = last_sequence + 1

        success = self.set_setting(db, setting_key, str(next_sequence))

        if not success:
            logger.critical(f"Failed to update invoice sequence number for key '{setting_key}' to '{next_sequence}'.")

        invoice_number = f"{prefix}{next_sequence:05d}"
        return invoice_number

settings_crud = SettingsCRUD()
