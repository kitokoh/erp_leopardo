from sqlalchemy import Column, Integer, String, Boolean
from db.connection import Base

class StatusSetting(Base):
    __tablename__ = 'StatusSettings'

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String, nullable=False)
    status_type = Column(String, nullable=False)
    color_hex = Column(String)
    icon_name = Column(String)
    default_duration_days = Column(Integer)
    is_archival_status = Column(Boolean, default=False)
    is_completion_status = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
