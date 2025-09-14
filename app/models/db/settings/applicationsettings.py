from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Applicationsettings(Base):
    __tablename__ = 'application_settings'
    setting_key = Column(Text, primary_key=True)
    setting_value = Column(Text)


    def __repr__(self):
        return f'<Applicationsettings setting_key={self.setting_key}>'
