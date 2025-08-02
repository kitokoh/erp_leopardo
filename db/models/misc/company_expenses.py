from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.connection import Base

class CompanyExpenses(Base):
    __tablename__ = 'company_expenses'
    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    expense_date = Column(Date, nullable=False)
    amount = Column(REAL, nullable=False)
    currency = Column(Text, nullable=False)
    recipient_name = Column(Text, nullable=False)
    description = Column(Text)
    facture_id = Column(Integer, unique=True, ForeignKey('company_factures.facture_id'))

    created_by_user_id = Column(Text, ForeignKey('users.user_id'))

    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Integer)
    deleted_at = Column(DateTime)


    def __repr__(self):
        return f'<CompanyExpenses expense_id={self.expense_id}>'
    company_facture_rel = relationship('CompanyFactures')
    user_rel = relationship('Users')
