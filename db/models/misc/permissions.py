from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Permission(Base):
    __tablename__ = 'permissions'

    permission_key = Column(String, primary_key=True)
    description = Column(Text)

    def __repr__(self):
        return f"<Permission(permission_key='{self.permission_key}')>"
