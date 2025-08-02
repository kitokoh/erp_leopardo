from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Reportconfigfields(Base):
    __tablename__ = 'report_config_fields'
    report_config_field_id = Column(Integer, primary_key=True, autoincrement=True)
    report_config_id = Column(Text, nullable=False, ForeignKey('reportconfigurations.report_config_id'))

    field_name = Column(Text, nullable=False)
    display_name = Column(Text)
    sort_order = Column(Integer)
    sort_direction = Column(Text)
    group_by_priority = Column(Integer)


    def __repr__(self):
        return f'<Reportconfigfields report_config_field_id={self.report_config_field_id}>'
    reportconfiguration_rel = relationship('Reportconfigurations')
