from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Moneytransferagents(Base):
    __tablename__ = 'money_transfer_agents'
    agent_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    agent_type = Column(Text, nullable=False)
    phone_number = Column(Text)
    email = Column(Text)
    country_id = Column(Text, ForeignKey('countries.country_id'))

    city_id = Column(Text, ForeignKey('cities.city_id'))

    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    is_deleted = Column(Integer)
    deleted_at = Column(Text)


    def __repr__(self):
        return f'<Moneytransferagents agent_id={self.agent_id}>'
    countrie_rel = relationship('Countries')
    citie_rel = relationship('Cities')
