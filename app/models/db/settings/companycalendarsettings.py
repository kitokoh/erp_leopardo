from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Companycalendarsettings(Base):
    __tablename__ = 'company_calendar_settings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey('users.user_id'), nullable=False, unique=True)
    business_type = Column(Text)
    activity_category = Column(Text)
    country_iso = Column(Text, nullable=False)
    region = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    user_rel = relationship('User')

    def __repr__(self):
        return f'<Companycalendarsettings id={self.id}>'
