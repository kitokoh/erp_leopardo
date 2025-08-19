from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.connection import Base

class BusinessUseCase(Base):
    __tablename__ = 'business_use_cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_profile_id = Column(Integer, ForeignKey('business_profile.id'))
    use_case_id = Column(Integer, ForeignKey('use_cases.id'))

    def __repr__(self):
        return f"<BusinessUseCase(id='{self.id}')>"
