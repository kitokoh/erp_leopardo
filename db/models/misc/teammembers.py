from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Teammembers(Base):
    __tablename__ = 'team_members'
    team_member_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, unique=True, ForeignKey('users.user_id'))

    full_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    role_or_title = Column(Text)
    department = Column(Text)
    phone_number = Column(Text)
    profile_picture_url = Column(Text)
    is_active = Column(Boolean)
    notes = Column(Text)
    hire_date = Column(Text)
    performance = Column(Integer)
    skills = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Teammembers team_member_id={self.team_member_id}>'
    user_rel = relationship('Users')
