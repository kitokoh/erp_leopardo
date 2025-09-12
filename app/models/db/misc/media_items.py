from sqlalchemy import Column, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from app.db.session_manager import Base

class MediaItem(Base):
    __tablename__ = 'media_items'

    media_item_id = Column(Text, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    item_type = Column(String(50))
    # Storing tags as a JSON array is flexible
    tags = Column(JSON)
    thumbnail_path = Column(String)
    # Storing metadata as a JSON object
    media_metadata = Column(JSON)
    # Filepath for local media like videos or images
    filepath = Column(String)
    # URL for linked media
    url = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<MediaItem(media_item_id='{self.media_item_id}', title='{self.title}')>"
