from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Sector(Base):
    __tablename__ = 'sectors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    type_association = Column(String)

    def __repr__(self):
        return f"<Sector(id='{self.id}')>"
