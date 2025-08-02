from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Permissions(Base):
    __tablename__ = 'permissions'
    permission_key = Column(Text, primary_key=True)
    description = Column(Text)


    def __repr__(self):
        return f'<Permissions permission_key={self.permission_key}>'
