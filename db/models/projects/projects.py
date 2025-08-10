from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Projects(Base):
    __tablename__ = 'projects'
    project_id = Column(String, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'))
    project_name = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    deadline_date = Column(Date)
    budget = Column(REAL)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    progress_percentage = Column(Integer)
    manager_team_member_id = Column(String, ForeignKey('team_members.team_member_id'))
    priority = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, server_default='0', nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    client_rel = relationship('Client')
    statussetting_rel = relationship('StatusSetting')
    user_rel = relationship('User')

    def __repr__(self):
        return f'<Projects project_id={self.project_id}>'
