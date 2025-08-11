from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.connection import Base

class RolePermissions(Base):
    __tablename__ = 'role_permissions'
    role_id = Column(Integer, ForeignKey('roles.role_id'), primary_key=True, nullable=False)
    permission_key = Column(Text, ForeignKey('permissions.permission_key'), primary_key=True, nullable=False)

    def __repr__(self):
        return f'<RolePermissions(role_id={self.role_id}, permission_key={self.permission_key})>'

    # Bidirectional relationship with back_populates
    role = relationship('Role', back_populates='permissions')
    permission = relationship('Permission', back_populates='roles')
