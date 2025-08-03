from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class CompanyExpense(Base):
    __tablename__ = 'company_expenses'

    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    expense_date = Column(Date)
    amount = Column(REAL)
    currency = Column(String)
    recipient_name = Column(String)
    description = Column(Text)
    facture_id = Column(Integer, ForeignKey('company_factures.facture_id'), unique=True)
    created_by_user_id = Column(String, ForeignKey('users.user_id'))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Integer)
    deleted_at = Column(DateTime)

    def __repr__(self):
        return f"<CompanyExpense(expense_id='{self.expense_id}')>"
