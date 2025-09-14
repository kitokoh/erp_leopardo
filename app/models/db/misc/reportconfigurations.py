from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class ReportConfiguration(Base):
    __tablename__ = 'report_configurations'

    report_config_id = Column(String, primary_key=True)
    report_name = Column(String)
    description = Column(Text)
    target_entity = Column(String)
    output_format = Column(String)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_system_report = Column(Boolean)

    def __repr__(self):
        return f"<ReportConfiguration(report_config_id='{self.report_config_id}')>"
