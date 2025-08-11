from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Text, ForeignKey('projects.project_id'), nullable=False)
    task_name = Column(String)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey('status_settings.status_id'))
    assignee_team_member_id = Column(Integer, ForeignKey('team_members.team_member_id'))
    reporter_team_member_id = Column(Integer, ForeignKey('team_members.team_member_id'))
    due_date = Column(Date)
    priority = Column(Integer)
    estimated_hours = Column(REAL)
    actual_hours_spent = Column(REAL)
    parent_task_id = Column(Integer, ForeignKey('tasks.task_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<Task(task_id='{self.task_id}')>"
