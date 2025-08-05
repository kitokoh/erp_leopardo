from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ActivityLog(Base):
    __tablename__ = 'activity_log'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    action_type = Column(String)
    details = Column(Text)
    related_entity_type = Column(String)
    related_entity_id = Column(String)
    related_client_id = Column(String, ForeignKey('clients.client_id'))
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ActivityLog(log_id='{self.log_id}')>"
