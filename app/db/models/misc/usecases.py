from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class UseCase(Base):
    __tablename__ = 'use_cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(Text)

    def __repr__(self):
        return f"<UseCase(id='{self.id}')>"
