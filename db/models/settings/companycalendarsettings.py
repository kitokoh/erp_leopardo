from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Companycalendarsettings(Base):
    __tablename__ = 'company_calendar_settings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False, unique=True, ForeignKey('users.user_id', ForeignKey('users.user_id'))
, ForeignKey('users.user_id'))


    business_type = Column(Text)
    activity_category = Column(Text)
    country_iso = Column(Text, nullable=False)
    region = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Companycalendarsettings id={self.id}>'
    user_rel = relationship('Users')
    user_rel = relationship('Users')
