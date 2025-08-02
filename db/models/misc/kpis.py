from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Kpis(Base):
    __tablename__ = 'kp_is'
    kpi_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    value = Column(REAL, nullable=False)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Kpis kpi_id={self.kpi_id}>'
    project_rel = relationship('Projects')
