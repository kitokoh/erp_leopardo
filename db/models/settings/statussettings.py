from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Statussettings(Base):
    __tablename__ = 'status_settings'
    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(Text, nullable=False)
    status_type = Column(Text, nullable=False)
    color_hex = Column(Text)
    icon_name = Column(Text)
    default_duration_days = Column(Integer)
    is_archival_status = Column(Boolean)
    is_completion_status = Column(Boolean)
    sort_order = Column(Integer)


    def __repr__(self):
        return f'<Statussettings status_id={self.status_id}>'
