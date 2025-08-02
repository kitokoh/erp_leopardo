from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Reportconfigfilters(Base):
    __tablename__ = 'report_config_filters'
    report_config_filter_id = Column(Integer, primary_key=True, autoincrement=True)
    report_config_id = Column(Text, nullable=False, ForeignKey('reportconfigurations.report_config_id'))

    field_name = Column(Text, nullable=False)
    operator = Column(Text, nullable=False)
    filter_value_1 = Column(Text)
    filter_value_2 = Column(Text)
    logical_group = Column(Text)


    def __repr__(self):
        return f'<Reportconfigfilters report_config_filter_id={self.report_config_filter_id}>'
    reportconfiguration_rel = relationship('Reportconfigurations')
