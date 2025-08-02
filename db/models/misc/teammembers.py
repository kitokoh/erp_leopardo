from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class TeamMember(Base):
    __tablename__ = 'team_members'

    team_member_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey('users.user_id'), unique=True)
    full_name = Column(String)
    email = Column(String)
    role_or_title = Column(String)
    department = Column(String)
    phone_number = Column(String)
    profile_picture_url = Column(String)
    is_active = Column(Boolean)
    notes = Column(Text)
    hire_date = Column(String)
    performance = Column(Integer)
    skills = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<TeamMember(team_member_id='{self.team_member_id}')>"
