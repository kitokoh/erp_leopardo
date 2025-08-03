from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class ReportConfigFilter(Base):
    __tablename__ = 'report_config_filters'

    report_config_filter_id = Column(Integer, primary_key=True, autoincrement=True)
    report_config_id = Column(Text, ForeignKey('report_configurations.report_config_id'), nullable=False)
    field_name = Column(String)
    operator = Column(String)
    filter_value_1 = Column(Text)
    filter_value_2 = Column(Text)
    logical_group = Column(String)

    def __repr__(self):
        return f"<ReportConfigFilter(report_config_filter_id='{self.report_config_filter_id}')>"
