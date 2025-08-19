from sqlalchemy import Column, Integer, String, Boolean
from app.db.connection import Base

class StatusSetting(Base):
    __tablename__ = 'status_settings'

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String, nullable=False)
    status_type = Column(String, nullable=False)
    color_hex = Column(String)
    icon_name = Column(String)
    default_duration_days = Column(Integer)
    is_archival_status = Column(Boolean, default=False)
    is_completion_status = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<StatusSetting(status_id={self.status_id}, status_name='{self.status_name}')>"
