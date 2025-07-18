from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, REAL, Text
from sqlalchemy.sql import func
from db.connection import Base

class Project(Base):
    __tablename__ = 'Projects'

    project_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('Clients.client_id'))
    project_name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(DateTime)
    deadline_date = Column(DateTime)
    budget = Column(REAL)
    status_id = Column(Integer, ForeignKey('StatusSettings.status_id'))
    progress_percentage = Column(Integer, default=0)
    manager_team_member_id = Column(String)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
