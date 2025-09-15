from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session_manager import Base

class TemplateCategory(Base):
    __tablename__ = 'template_categories'
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    purpose = Column(Text)


    def __repr__(self):
        return f'<Templatecategories category_id={self.category_id}>'
