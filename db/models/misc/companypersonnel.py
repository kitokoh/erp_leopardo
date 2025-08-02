from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Companypersonnel(Base):
    __tablename__ = 'company_personnel'
    personnel_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Text, nullable=False, ForeignKey('companies.company_id'))

    name = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    created_at = Column(DateTime)


    def __repr__(self):
        return f'<Companypersonnel personnel_id={self.personnel_id}>'
    companie_rel = relationship('Companies')
