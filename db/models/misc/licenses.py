from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Licenses(Base):
    __tablename__ = 'licenses'
    license_id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False, ForeignKey('users.user_id'))

    license_type = Column(Text, nullable=False)
    license_key = Column(Text, unique=True)
    activation_date = Column(DateTime)
    expiration_date = Column(DateTime)
    machine_info = Column(Text)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Licenses license_id={self.license_id}>'
    user_rel = relationship('Users')
