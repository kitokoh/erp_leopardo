from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Reportconfigurations(Base):
    __tablename__ = 'report_configurations'
    report_config_id = Column(Text, primary_key=True)
    report_name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    target_entity = Column(Text, nullable=False)
    output_format = Column(Text, nullable=False)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_system_report = Column(Boolean)


    def __repr__(self):
        return f'<Reportconfigurations report_config_id={self.report_config_id}>'
    user_rel = relationship('Users')
