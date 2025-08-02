from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Tasks(Base):
    __tablename__ = 'tasks'
    task_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Text, nullable=False, ForeignKey('projects.project_id'))

    task_name = Column(Text, nullable=False)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey('statussettings.status_id'))

    assignee_team_member_id = Column(Integer, ForeignKey('teammembers.team_member_id'))

    reporter_team_member_id = Column(Integer, ForeignKey('teammembers.team_member_id'))

    due_date = Column(Date)
    priority = Column(Integer)
    estimated_hours = Column(REAL)
    actual_hours_spent = Column(REAL)
    parent_task_id = Column(Integer, ForeignKey('tasks.task_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    completed_at = Column(DateTime)


    def __repr__(self):
        return f'<Tasks task_id={self.task_id}>'
    project_rel = relationship('Projects')
    statussetting_rel = relationship('Statussettings')
    teammember_rel = relationship('Teammembers')
    teammember_rel = relationship('Teammembers')
    task_rel = relationship('Tasks')
