import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class PerformanceReviewStatusEnum(enum.Enum):
    DRAFT = "draft"
    PENDING_EMPLOYEE_REVIEW = "pending_employee_review"
    PENDING_MANAGER_REVIEW = "pending_manager_review"
    COMPLETED = "completed"

performance_review_goals_link = Table('performance_review_goals_link', Base.metadata,
    Column('performance_review_id', Integer, ForeignKey('performance_reviews.id'), primary_key=True),
    Column('goal_id', Integer, ForeignKey('goals.id'), primary_key=True)
)

class PerformanceReview(Base):
    __tablename__ = 'performance_reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, ForeignKey('employees.id'), nullable=False, index=True)
    reviewer_id = Column(String, ForeignKey('users.user_id'), nullable=True, index=True)
    review_cycle_id = Column(Integer, ForeignKey('review_cycles.id'), nullable=True)
    review_date = Column(DateTime, nullable=True)
    overall_rating = Column(Integer, nullable=True)
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    employee_comments = Column(Text, nullable=True)
    manager_comments = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(PerformanceReviewStatusEnum), nullable=False, default=PerformanceReviewStatusEnum.DRAFT)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    employee = relationship("Employee")
    reviewer = relationship("User")
    review_cycle = relationship("ReviewCycle")
    goals_reviewed = relationship("Goal", secondary=performance_review_goals_link, backref="performance_reviews")

    def __repr__(self):
        return f"<PerformanceReview(id={self.id}, employee_id='{self.employee_id}', status='{self.status.value if self.status else None}')>"
