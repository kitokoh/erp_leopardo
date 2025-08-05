from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ReportConfigField(Base):
    __tablename__ = 'report_config_fields'

    report_config_field_id = Column(Integer, primary_key=True, autoincrement=True)
    report_config_id = Column(Text, ForeignKey('report_configurations.report_config_id'), nullable=False)
    field_name = Column(String)
    display_name = Column(String)
    sort_order = Column(Integer)
    sort_direction = Column(String)
    group_by_priority = Column(Integer)

    def __repr__(self):
        return f"<ReportConfigField(report_config_field_id='{self.report_config_field_id}')>"
