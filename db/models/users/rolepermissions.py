from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Rolepermissions(Base):
    __tablename__ = 'role_permissions'
    role_id = Column(Integer, nullable=False, ForeignKey('roles.role_id'))

    permission_key = Column(Text, nullable=False, ForeignKey('permissions.permission_key'))



    def __repr__(self):
        return f'<Rolepermissions role_id={self.role_id}>'
    role_rel = relationship('Roles')
    permission_rel = relationship('Permissions')
