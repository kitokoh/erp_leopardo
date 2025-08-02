from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Referents(Base):
    __tablename__ = 'referents'
    referent_id = Column(Text, primary_key=True)
    client_id = Column(Text, nullable=False, unique=True, ForeignKey('clients.client_id'))

    country_id = Column(Integer, nullable=False, ForeignKey('countries.country_id'))

    region_id = Column(Integer, ForeignKey('regions.region_id'))

    city_id = Column(Integer, ForeignKey('cities.city_id'))

    referent_since = Column(DateTime)
    notes = Column(Text)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    created_by_user_id = Column(Text, ForeignKey('users.user_id'))



    def __repr__(self):
        return f'<Referents referent_id={self.referent_id}>'
    client_rel = relationship('Clients')
    countrie_rel = relationship('Countries')
    region_rel = relationship('Regions')
    citie_rel = relationship('Cities')
    user_rel = relationship('Users')
