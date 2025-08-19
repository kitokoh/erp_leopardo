from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class ContactSyncLog(Base):
    __tablename__ = 'contact_sync_log'

    sync_log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_google_account_id = Column(Text, ForeignKey('user_google_accounts.user_google_account_id'))
    local_contact_id = Column(Text)
    local_contact_type = Column(Text)
    google_contact_id = Column(Text)
    platform_etag = Column(Text)
    google_etag = Column(Text)
    last_sync_timestamp = Column(DateTime)
    sync_status = Column(Text)
    sync_direction = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<ContactSyncLog(sync_log_id='{self.sync_log_id}')>"
