from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .role import Role
from db.connection import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    is_active = Column(Boolean, server_default='1', nullable=False)
    is_deleted = Column(Integer, server_default='0', nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    is_fingerprint_auth_enabled = Column(Boolean, server_default='0', nullable=True)
    fingerprint_template_id = Column(Text, nullable=True)
    is_face_auth_enabled = Column(Boolean, server_default='0', nullable=True)
    face_template_id = Column(Text, nullable=True)
    is_voice_auth_enabled = Column(Boolean, server_default='0', nullable=True)
    voice_profile_id = Column(Text, nullable=True)

    role = relationship("Role")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"
