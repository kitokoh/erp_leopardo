from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.connection import Base

class EmployeeDocument(Base):
    __tablename__ = 'employee_documents'

    id = Column(String, primary_key=True)
    employee_id = Column(String, ForeignKey('employees.id'))
    document_category_id = Column(Integer, ForeignKey('document_categories.id'))
    file_name = Column(String)
    file_path_or_key = Column(String)
    file_type = Column(String)
    file_size = Column(Integer)
    description = Column(Text)
    uploaded_at = Column(DateTime)
    uploaded_by_id = Column(String, ForeignKey('users.user_id'))

    employee = relationship("Employee")
    document_category = relationship("DocumentCategory")
    uploaded_by = relationship("User")

    def __repr__(self):
        return f"<EmployeeDocument(id='{self.id}', file_name='{self.file_name}')>"
