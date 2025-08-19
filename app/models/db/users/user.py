from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, true, false
from app.models.db.users.role import Role
from app.db.connection import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    is_active = Column(Boolean, server_default=true(), nullable=False)
    is_deleted = Column(Boolean, server_default=false(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    is_fingerprint_auth_enabled = Column(Boolean, server_default=false(), nullable=True)
    fingerprint_template_id = Column(Text, nullable=True)
    is_face_auth_enabled = Column(Boolean, server_default=false(), nullable=True)
    face_template_id = Column(Text, nullable=True)
    is_voice_auth_enabled = Column(Boolean, server_default=false(), nullable=True)
    voice_profile_id = Column(Text, nullable=True)

    role = relationship("Role", back_populates="users")
    google_accounts = relationship('UserGoogleAccounts', back_populates='user', cascade="all, delete-orphan")
    __table_args__ = {'extend_existing': True}

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"
