from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, REAL, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Project(Base):
    __tablename__ = 'projects'

    project_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    project_name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    deadline_date = Column(Date)
    budget = Column(REAL)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    progress_percentage = Column(Integer, default=0)
    manager_team_member_id = Column(String, ForeignKey('team_members.team_member_id'))
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    client = relationship("Client")
    status = relationship("StatusSetting")
    manager = relationship("TeamMember")

    def __repr__(self):
        return f"<Project(project_id='{self.project_id}', project_name='{self.project_name}')>"
