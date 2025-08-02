from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Companies(Base):
    __tablename__ = 'companies'
    # = Column(String, primary_key=True)
    # = Column(String, nullable=False)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(String)
    # = Column(Date)


    def __repr__(self):
        return f'<Companies #={self.#}>'
