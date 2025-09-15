from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class Permission(Base):
    __tablename__ = 'permissions'

    permission_key = Column(String, primary_key=True)
    description = Column(Text)

    roles = relationship('RolePermissions', back_populates='permission', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Permission(permission_key='{self.permission_key}')>"
