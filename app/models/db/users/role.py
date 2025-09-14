from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session_manager import Base

from sqlalchemy.orm import relationship

class Role(Base):
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship('RolePermissions', back_populates='role', cascade="all, delete-orphan")
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"
