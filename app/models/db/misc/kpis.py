from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, REAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Kpi(Base):
    __tablename__ = 'kp_is'

    kpi_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey('projects.project_id'))
    name = Column(String)
    value = Column(REAL)
    target = Column(REAL)
    trend = Column(String)
    unit = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Kpi(kpi_id='{self.kpi_id}')>"
