from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class Menuconfiguration(Base):
    __tablename__ = 'menu_configuration'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, nullable=False)
    item_name = Column(Text, nullable=False)
    item_order = Column(Integer, nullable=False)
    is_visible = Column(Boolean)
    module_identifier = Column(Text)
    parent_id = Column(Integer)


    def __repr__(self):
        return f'<Menuconfiguration id={self.id}>'
