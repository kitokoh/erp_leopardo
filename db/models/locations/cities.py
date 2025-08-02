from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Cities(Base):
    __tablename__ = 'cities'
    city_id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, nullable=False, ForeignKey('countries.country_id'))

    city_name = Column(Text, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


    def __repr__(self):
        return f'<Cities city_id={self.city_id}>'
    countrie_rel = relationship('Countries')
