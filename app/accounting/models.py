import uuid
import enum
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey,
    Enum as SQLAlchemyEnum, UniqueConstraint, Boolean, Date, Table, Numeric
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime

# SQLAlchemy Base for accounting module
# It's good practice to have a Base per module if they are somewhat independent,
# or use a shared Base from a central location (e.g., app.db.base.Base)
# For now, let's define it here. If a central Base exists, this should be updated.
from db.session_manager import Base

# --- Enum Definitions ---

class AccountTypeEnum(enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"
    COST_OF_GOODS_SOLD = "cost_of_goods_sold" # CoGS
    OTHER_INCOME = "other_income"
    OTHER_EXPENSE = "other_expense"

class FinancialStatementTypeEnum(enum.Enum):
    BALANCE_SHEET = "balance_sheet"
    PROFIT_AND_LOSS = "profit_and_loss" # Income Statement
    CASH_FLOW_STATEMENT = "cash_flow_statement"
    TRIAL_BALANCE = "trial_balance" # Not strictly a financial statement, but often grouped

class TaxTypeEnum(enum.Enum):
    VAT = "vat"
    SALES_TAX = "sales_tax"
    INCOME_TAX = "income_tax"
    OTHER = "other"

class FiscalYearStatusEnum(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING_CLOSURE = "pending_closure"


# --- SQLAlchemy Models ---

class ChartOfAccounts(Base):
    __tablename__ = "acc_chart_of_accounts"
    __table_args__ = {'extend_existing': True}
    # __table_args__ = {'schema': 'accounting'} # Removed for SQLite compatibility

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True) # e.g., "1010", "4000"
    name = Column(String, nullable=False, index=True)
    account_type = Column(SQLAlchemyEnum(AccountTypeEnum), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_id = Column(String, ForeignKey(f"{__tablename__}.id"), nullable=True) # Self-referential for hierarchy

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    parent = relationship("ChartOfAccounts", remote_side=[id], backref="children")
    journal_items = relationship("JournalItem", back_populates="account")

    def __repr__(self):
        return f"<ChartOfAccounts(code='{self.code}', name='{self.name}')>"

class JournalEntry(Base):
    __tablename__ = "acc_journal_entries"
    __table_args__ = {'extend_existing': True}
    # __table_args__ = {'schema': 'accounting'} # Removed for SQLite compatibility

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    reference_number = Column(String, nullable=True, index=True) # e.g., Invoice number, Payment ID
    fiscal_year_id = Column(String, ForeignKey("acc_fiscal_years.id"), nullable=False)
    # user_id = Column(String, ForeignKey('users.user_id'), nullable=True) # Assuming a Users table exists in the public schema or similar

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # created_by = relationship("User") # Needs User model defined and imported

    items = relationship("JournalItem", back_populates="journal_entry", cascade="all, delete-orphan")
    fiscal_year = relationship("FiscalYear", back_populates="journal_entries")


    def __repr__(self):
        return f"<JournalEntry(id='{self.id}', date='{self.entry_date}', description='{self.description[:30]}...')>"

class JournalItem(Base):
    __tablename__ = "acc_journal_items"
    # __table_args__ = {'schema': 'accounting'} # Original schema arg commented out

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_entry_id = Column(String, ForeignKey("acc_journal_entries.id"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("acc_chart_of_accounts.id"), nullable=False, index=True)
    # Using Numeric for precision with currency values
    debit_amount = Column(Numeric(precision=18, scale=2), nullable=False, default=0.00)
    credit_amount = Column(Numeric(precision=18, scale=2), nullable=False, default=0.00)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    journal_entry = relationship("JournalEntry", back_populates="items")
    account = relationship("ChartOfAccounts", back_populates="journal_items")

    __table_args__ = (
        UniqueConstraint('journal_entry_id', 'account_id', 'debit_amount', 'credit_amount', name='uq_journal_item_detail'),
        {'extend_existing': True},
    )

    def __repr__(self):
        return f"<JournalItem(account_id='{self.account_id}', debit={self.debit_amount}, credit={self.credit_amount})>"

class FinancialStatement(Base):
    __tablename__ = "acc_financial_statements"
    __table_args__ = {'extend_existing': True}
    # __table_args__ = {'schema': 'accounting'} # Removed for SQLite compatibility

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False) # e.g., "Balance Sheet Q1 2023"
    statement_type = Column(SQLAlchemyEnum(FinancialStatementTypeEnum), nullable=False)
    fiscal_year_id = Column(String, ForeignKey("acc_fiscal_years.id"), nullable=False)
    period_start_date = Column(Date, nullable=False)
    period_end_date = Column(Date, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_json = Column(Text, nullable=False) # Store the report data as JSON

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # generated_by_user_id = Column(String, ForeignKey('users.user_id'), nullable=True)

    fiscal_year = relationship("FiscalYear", back_populates="financial_statements")

    def __repr__(self):
        return f"<FinancialStatement(name='{self.name}', type='{self.statement_type.value}')>"

class TaxRate(Base):
    __tablename__ = "acc_tax_rates"
    __table_args__ = {'extend_existing': True}
    # __table_args__ = {'schema': 'accounting'} # Removed for SQLite compatibility

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True) # e.g., "Standard VAT", "Reduced Sales Tax"
    rate_percentage = Column(Numeric(precision=5, scale=2), nullable=False) # e.g., 20.00 for 20%
    tax_type = Column(SQLAlchemyEnum(TaxTypeEnum), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    # country_code = Column(String(2), nullable=True) # Optional: For country-specific taxes

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<TaxRate(name='{self.name}', rate='{self.rate_percentage}%')>"

class Currency(Base):
    __tablename__ = "acc_currencies"
    __table_args__ = {'extend_existing': True}
    # __table_args__ = {'schema': 'accounting'} # Removed for SQLite compatibility

    code = Column(String(3), primary_key=True) # e.g., "USD", "EUR", "JPY"
    name = Column(String, nullable=False, unique=True) # e.g., "US Dollar", "Euro"
    symbol = Column(String(5), nullable=True) # e.g., "$", "€"
    exchange_rate_to_base = Column(Numeric(precision=18, scale=6), nullable=True) # Rate against a base currency (e.g., USD or company's main currency)
    is_base_currency = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Currency(code='{self.code}', name='{self.name}')>"

class FiscalYear(Base):
    __tablename__ = "acc_fiscal_years"
    __table_args__ = {'extend_existing': True}
    # __table_args__ = {'schema': 'accounting'} # Removed for SQLite compatibility

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True) # e.g., "FY2023", "Fiscal Year 2023-2024"
    start_date = Column(Date, nullable=False, unique=True)
    end_date = Column(Date, nullable=False, unique=True)
    status = Column(SQLAlchemyEnum(FiscalYearStatusEnum), nullable=False, default=FiscalYearStatusEnum.OPEN)
    is_closed_for_accounting = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    # closed_by_user_id = Column(String, ForeignKey('users.user_id'), nullable=True)
    # closed_at = Column(DateTime(timezone=True), nullable=True)

    journal_entries = relationship("JournalEntry", back_populates="fiscal_year")
    financial_statements = relationship("FinancialStatement", back_populates="fiscal_year")

    def __repr__(self):
        return f"<FiscalYear(name='{self.name}', start='{self.start_date}', end='{self.end_date}')>"


# --- Pydantic Models ---

# Helper for Decimal fields in Pydantic
from decimal import Decimal

# --- FiscalYear Pydantic Models ---
class FiscalYearBase(BaseModel):
    name: str = Field(..., example="FY2024")
    start_date: date
    end_date: date
    status: Optional[FiscalYearStatusEnum] = FiscalYearStatusEnum.OPEN
    is_closed_for_accounting: Optional[bool] = False

class FiscalYearCreate(FiscalYearBase):
    pass

class FiscalYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[FiscalYearStatusEnum] = None
    is_closed_for_accounting: Optional[bool] = None

class FiscalYearRead(FiscalYearBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Currency Pydantic Models ---
class CurrencyBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, example="USD")
    name: str = Field(..., example="US Dollar")
    symbol: Optional[str] = Field(None, example="$")
    exchange_rate_to_base: Optional[Decimal] = Field(None, example=1.000000)
    is_base_currency: Optional[bool] = False

class CurrencyCreate(CurrencyBase):
    pass

class CurrencyUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    exchange_rate_to_base: Optional[Decimal] = None
    is_base_currency: Optional[bool] = None

class CurrencyRead(CurrencyBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- TaxRate Pydantic Models ---
class TaxRateBase(BaseModel):
    name: str = Field(..., example="VAT Standard")
    rate_percentage: Decimal = Field(..., example=20.00, decimal_places=2)
    tax_type: TaxTypeEnum
    description: Optional[str] = None
    is_active: Optional[bool] = True

class TaxRateCreate(TaxRateBase):
    pass

class TaxRateUpdate(BaseModel):
    name: Optional[str] = None
    rate_percentage: Optional[Decimal] = Field(None, decimal_places=2)
    tax_type: Optional[TaxTypeEnum] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class TaxRateRead(TaxRateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- ChartOfAccounts Pydantic Models ---
class ChartOfAccountsBase(BaseModel):
    code: str = Field(..., example="10100")
    name: str = Field(..., example="Cash on Hand")
    account_type: AccountTypeEnum
    description: Optional[str] = None
    is_active: Optional[bool] = True
    parent_id: Optional[str] = None

class ChartOfAccountsCreate(ChartOfAccountsBase):
    pass

class ChartOfAccountsUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    account_type: Optional[AccountTypeEnum] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    parent_id: Optional[str] = None # Allow reparenting or setting to None

class ChartOfAccountsRead(ChartOfAccountsBase):
    id: str
    created_at: datetime
    updated_at: datetime
    # children: List['ChartOfAccountsRead'] = [] # Enable if needed, ensure proper recursion handling

    class Config:
        from_attributes = True

# ChartOfAccountsRead.model_rebuild() # For self-referencing Pydantic models

# --- JournalItem Pydantic Models ---
class JournalItemBase(BaseModel):
    account_id: str = Field(..., example="uuid_of_cash_account")
    debit_amount: Decimal = Field(default=0.00, ge=0, decimal_places=2)
    credit_amount: Decimal = Field(default=0.00, ge=0, decimal_places=2)
    description: Optional[str] = None

    # Validator to ensure that not both debit and credit are zero, or both non-zero
    # This might be better handled in service layer logic depending on complexity
    @model_validator(mode='after')
    def check_debit_credit_logic(self) -> 'JournalItemBase':
        if self.debit_amount == 0 and self.credit_amount == 0:
            # Allow items to be zero if they are part of a larger entry that balances.
            # This specific validation might be too restrictive at item level if entry must balance.
            # However, an item itself being all zero is often an error.
            # For now, let's keep it to prevent all-zero items.
            pass # Re-evaluating this: an item can be zero if it's a placeholder or will be adjusted.
                 # The balancing should happen at JournalEntry level.
                 # Let's remove the strict non-zero check here.

        if self.debit_amount != 0 and self.credit_amount != 0:
            raise ValueError('Debit and credit amounts cannot both be non-zero for a single journal item.')
        return self

class JournalItemCreate(JournalItemBase):
    pass

class JournalItemRead(JournalItemBase):
    id: str
    journal_entry_id: str
    created_at: datetime
    account: Optional[ChartOfAccountsRead] = None # Optional: for richer responses

    class Config:
        from_attributes = True

# --- JournalEntry Pydantic Models ---
class JournalEntryBase(BaseModel):
    entry_date: date
    description: str = Field(..., example="Payment for office supplies")
    reference_number: Optional[str] = Field(None, example="INV-2023-001")
    fiscal_year_id: str = Field(..., example="uuid_of_fiscal_year")
    # user_id: Optional[str] = None # If tracking user who created

class JournalEntryCreate(JournalEntryBase):
    items: List[JournalItemCreate]

    # Validator to ensure debits equal credits for the entry
    @model_validator(mode='after')
    def check_debits_equal_credits(self) -> 'JournalEntryCreate':
        total_debits = sum(item.debit_amount for item in self.items)
        total_credits = sum(item.credit_amount for item in self.items)
        if total_debits != total_credits:
            raise ValueError('Total debits must equal total credits for the journal entry.')
        if not self.items:
            raise ValueError('Journal entry must have at least one item.')
        return self

class JournalEntryUpdate(BaseModel):
    entry_date: Optional[date] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    fiscal_year_id: Optional[str] = None
    # user_id: Optional[str] = None
    # items: Optional[List[JournalItemUpdate]] # Updating items can be complex, often handled by dedicated endpoints

class JournalEntryRead(JournalEntryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    items: List[JournalItemRead] = []
    fiscal_year: Optional[FiscalYearRead] = None # Optional: for richer responses
    # created_by: Optional[UserRead] = None # If User model is available

    class Config:
        from_attributes = True


# --- FinancialStatement Pydantic Models ---
class FinancialStatementBase(BaseModel):
    name: str = Field(..., example="Balance Sheet - Q1 2024")
    statement_type: FinancialStatementTypeEnum
    fiscal_year_id: str
    period_start_date: date
    period_end_date: date
    data_json: Dict[str, Any] # Or str if JSON string is stored directly

class FinancialStatementCreate(FinancialStatementBase):
    pass

class FinancialStatementUpdate(BaseModel):
    name: Optional[str] = None
    # statement_type, fiscal_year_id, period dates are usually not updatable for a generated statement
    # data_json might be updated if a regeneration occurs, but usually a new statement is created.

class FinancialStatementRead(FinancialStatementBase):
    id: str
    generated_at: datetime
    created_at: datetime
    fiscal_year: Optional[FiscalYearRead] = None # Optional

    class Config:
        from_attributes = True

# Rebuild models that have forward references if any (like ChartOfAccountsRead for its children)
# This is typically needed if you have List['Self'] type hints.
# ChartOfAccountsRead.model_rebuild()
# Not strictly necessary here as children is commented out but good practice if it were enabled.
