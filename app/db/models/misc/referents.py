from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class Referent(Base):
    __tablename__ = 'referents'

    referent_id = Column(String, primary_key=True)
    client_id = Column(Text, ForeignKey('clients.client_id'), nullable=False, unique=True)
    country_id = Column(Integer, ForeignKey('countries.country_id'), nullable=False)
    region_id = Column(Integer, ForeignKey('regions.region_id'))
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    referent_since = Column(DateTime)
    notes = Column(Text)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))

    def __repr__(self):
        return f"<Referent(referent_id='{self.referent_id}')>"
