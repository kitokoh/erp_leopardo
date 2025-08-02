from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Sectors(Base):
    __tablename__ = 'sectors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    type_association = Column(Text, nullable=False)


    def __repr__(self):
        return f'<Sectors id={self.id}>'
