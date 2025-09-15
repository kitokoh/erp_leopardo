from sqlalchemy import Column, Integer, String
from app.db.session_manager import Base

class Tag(Base):
    __tablename__ = 'tags'

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Tag(tag_name='{self.tag_name}')>"
