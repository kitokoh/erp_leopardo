from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class License(Base):
    __tablename__ = 'licenses'

    license_id = Column(String, primary_key=True)
    user_id = Column(Text, ForeignKey('users.user_id'), nullable=False)
    license_type = Column(String)
    license_key = Column(String)
    activation_date = Column(DateTime)
    expiration_date = Column(DateTime)
    machine_info = Column(Text)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<License(license_id='{self.license_id}')>"
