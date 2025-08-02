from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Regions(Base):
    __tablename__ = 'regions'
    region_id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(Text, nullable=False)
    country_id = Column(Integer, nullable=False, ForeignKey('countries.country_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Regions region_id={self.region_id}>'
    countrie_rel = relationship('Countries')
