from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from db.connection import Base

class Role(Base):
    __tablename__ = 'roles'

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Role(role_id={self.role_id}, role_name='{self.role_name}')>"
