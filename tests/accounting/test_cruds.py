import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from decimal import Decimal
from datetime import date, datetime

# Assuming your models and cruds are structured as:
# accounting.models (SQLAlchemy and Pydantic)
# accounting.cruds
# api.models (for the main Base)
# Adjust imports based on your actual project structure
from accounting import models as acc_models
from accounting import cruds as acc_cruds
from api.models import Base as MainBase # The Base used by accounting models if it's shared

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    # Create all tables defined in the MainBase metadata (which should include accounting tables)
    # This assumes accounting models are correctly associated with a Base that's known here.
    # If accounting models use their own Base, that needs to be created too.
    # For simplicity, assuming accounting models use the same Base as imported or a derivative.

    # If accounting models are defined with `accounting.models.Base` and it's separate:
    # acc_models.Base.metadata.create_all(bind=engine)
    # Else, if they use a shared Base (e.g., from api.models.Base):
    MainBase.metadata.create_all(bind=engine) # This creates all tables known to MainBase
                                            # Ensure accounting tables are correctly registered with this Base.
                                            # If `__table_args__ = {'schema': 'accounting'}` was used,
                                            # SQLite will create tables like `accounting_table_name`.

    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        # Drop all tables after each test function
        # acc_models.Base.metadata.drop_all(bind=engine) # If separate Base
        MainBase.metadata.drop_all(bind=engine)


# --- FiscalYear CRUD Tests ---
def test_create_fiscal_year(db: Session):
    fy_in = acc_models.FiscalYearCreate(name="FY2023", start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))
    fy = acc_cruds.fiscal_year.create(db, obj_in=fy_in)
    assert fy is not None
    assert fy.name == "FY2023"
    assert fy.start_date == date(2023, 1, 1)
    assert fy.status == acc_models.FiscalYearStatusEnum.OPEN

def test_get_fiscal_year(db: Session):
    fy_in = acc_models.FiscalYearCreate(name="FY2024", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
    created_fy = acc_cruds.fiscal_year.create(db, obj_in=fy_in)

    retrieved_fy = acc_cruds.fiscal_year.get(db, id=created_fy.id)
    assert retrieved_fy is not None
    assert retrieved_fy.id == created_fy.id
    assert retrieved_fy.name == "FY2024"

def test_get_fiscal_year_by_name(db: Session):
    fy_in = acc_models.FiscalYearCreate(name="FY2025_Test", start_date=date(2025,1,1), end_date=date(2025,12,31))
    acc_cruds.fiscal_year.create(db, obj_in=fy_in)
    retrieved_fy = acc_cruds.fiscal_year.get_by_name(db, name="FY2025_Test")
    assert retrieved_fy is not None
    assert retrieved_fy.name == "FY2025_Test"

def test_get_fiscal_year_by_date(db: Session):
    fy_in = acc_models.FiscalYearCreate(name="FY_DateTest", start_date=date(2023, 6, 1), end_date=date(2024, 5, 31))
    acc_cruds.fiscal_year.create(db, obj_in=fy_in)
    target_date = date(2023, 10, 15)
    retrieved_fy = acc_cruds.fiscal_year.get_by_date(db, target_date=target_date)
    assert retrieved_fy is not None
    assert retrieved_fy.name == "FY_DateTest"
    assert retrieved_fy.start_date <= target_date <= retrieved_fy.end_date

def test_update_fiscal_year(db: Session):
    fy_in = acc_models.FiscalYearCreate(name="FY_Update", start_date=date(2023,1,1), end_date=date(2023,12,31))
    created_fy = acc_cruds.fiscal_year.create(db, obj_in=fy_in)

    update_data = acc_models.FiscalYearUpdate(status=acc_models.FiscalYearStatusEnum.CLOSED, is_closed_for_accounting=True)
    updated_fy = acc_cruds.fiscal_year.update(db, db_obj=created_fy, obj_in=update_data)

    assert updated_fy.status == acc_models.FiscalYearStatusEnum.CLOSED
    assert updated_fy.is_closed_for_accounting is True
    assert updated_fy.name == "FY_Update" # Name should not change unless specified

# --- Currency CRUD Tests ---
def test_create_currency(db: Session):
    currency_in = acc_models.CurrencyCreate(code="EUR", name="Euro", symbol="€", exchange_rate_to_base=Decimal("0.92"))
    curr = acc_cruds.currency.create(db, obj_in=currency_in)
    assert curr is not None
    assert curr.code == "EUR"
    assert curr.name == "Euro"

def test_get_currency(db: Session):
    currency_in = acc_models.CurrencyCreate(code="GBP", name="British Pound", symbol="£")
    acc_cruds.currency.create(db, obj_in=currency_in)
    retrieved_curr = acc_cruds.currency.get(db, id="GBP")
    assert retrieved_curr is not None
    assert retrieved_curr.code == "GBP"

def test_set_base_currency(db: Session):
    acc_cruds.currency.create(db, obj_in=acc_models.CurrencyCreate(code="USD", name="US Dollar", is_base_currency=False))
    acc_cruds.currency.create(db, obj_in=acc_models.CurrencyCreate(code="CAD", name="Canadian Dollar", is_base_currency=False))

    acc_cruds.currency.set_base_currency(db, currency_code="CAD")
    base_curr = acc_cruds.currency.get_base_currency(db)
    assert base_curr is not None
    assert base_curr.code == "CAD"

    usd_curr = acc_cruds.currency.get(db, id="USD")
    assert usd_curr is not None
    assert usd_curr.is_base_currency is False


# --- TaxRate CRUD Tests ---
def test_create_tax_rate(db: Session):
    tax_in = acc_models.TaxRateCreate(name="VAT 20%", rate_percentage=Decimal("20.00"), tax_type=acc_models.TaxTypeEnum.VAT)
    tax = acc_cruds.tax_rate.create(db, obj_in=tax_in)
    assert tax is not None
    assert tax.name == "VAT 20%"
    assert tax.rate_percentage == Decimal("20.00")

# --- ChartOfAccounts CRUD Tests ---
def test_create_chart_of_account(db: Session):
    acc_in = acc_models.ChartOfAccountsCreate(code="10100", name="Cash", account_type=acc_models.AccountTypeEnum.ASSET)
    acc = acc_cruds.chart_of_accounts.create(db, obj_in=acc_in)
    assert acc is not None
    assert acc.code == "10100"
    assert acc.name == "Cash"

def test_create_child_account(db: Session):
    parent_in = acc_models.ChartOfAccountsCreate(code="10000", name="Assets", account_type=acc_models.AccountTypeEnum.ASSET)
    parent_acc = acc_cruds.chart_of_accounts.create(db, obj_in=parent_in)

    child_in = acc_models.ChartOfAccountsCreate(code="10100", name="Cash", account_type=acc_models.AccountTypeEnum.ASSET, parent_id=parent_acc.id)
    child_acc = acc_cruds.chart_of_accounts.create(db, obj_in=child_in)

    assert child_acc is not None
    assert child_acc.parent_id == parent_acc.id
    retrieved_parent = db.query(acc_models.ChartOfAccounts).filter(acc_models.ChartOfAccounts.id == parent_acc.id).one()
    assert child_acc in retrieved_parent.children


# --- JournalEntry and JournalItem CRUD Tests ---
@pytest.fixture
def setup_basic_accounting_data(db: Session) -> dict:
    fy = acc_cruds.fiscal_year.create(db, obj_in=acc_models.FiscalYearCreate(name="FY_JournalTest", start_date=date(2023,1,1), end_date=date(2023,12,31)))
    cash_acc = acc_cruds.chart_of_accounts.create(db, obj_in=acc_models.ChartOfAccountsCreate(code="1010", name="Cash", account_type=acc_models.AccountTypeEnum.ASSET))
    revenue_acc = acc_cruds.chart_of_accounts.create(db, obj_in=acc_models.ChartOfAccountsCreate(code="4010", name="Sales Revenue", account_type=acc_models.AccountTypeEnum.REVENUE))
    expense_acc = acc_cruds.chart_of_accounts.create(db, obj_in=acc_models.ChartOfAccountsCreate(code="5010", name="Office Expense", account_type=acc_models.AccountTypeEnum.EXPENSE))
    return {"fy": fy, "cash": cash_acc, "revenue": revenue_acc, "expense": expense_acc}

def test_create_journal_entry_with_items_balanced(db: Session, setup_basic_accounting_data):
    data = setup_basic_accounting_data
    items_in = [
        acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("100.00")),
        acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("100.00")),
    ]
    entry_in = acc_models.JournalEntryCreate(
        entry_date=date(2023, 3, 15),
        description="Received payment for services",
        fiscal_year_id=data["fy"].id,
        items=items_in
    )

    created_entry = acc_cruds.journal_entry.create_with_items(db, obj_in=entry_in)
    assert created_entry is not None
    assert created_entry.description == "Received payment for services"
    assert len(created_entry.items) == 2

    retrieved_items = sorted(created_entry.items, key=lambda x: x.account_id) # Sort for consistent assertion
    cash_item = next(i for i in retrieved_items if i.account_id == data["cash"].id)
    revenue_item = next(i for i in retrieved_items if i.account_id == data["revenue"].id)

    assert cash_item.debit_amount == Decimal("100.00")
    assert cash_item.credit_amount == Decimal("0.00")
    assert revenue_item.credit_amount == Decimal("100.00")
    assert revenue_item.debit_amount == Decimal("0.00")


def test_create_journal_entry_unbalanced_raises_error(db: Session, setup_basic_accounting_data):
    data = setup_basic_accounting_data
    items_in = [
        acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("100.00")),
        acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("90.00")), # Unbalanced
    ]
    entry_in = acc_models.JournalEntryCreate(
        entry_date=date(2023,3,16), description="Test unbalanced", fiscal_year_id=data["fy"].id, items=items_in
    )
    with pytest.raises(ValueError, match="Total debits must equal total credits"):
        acc_cruds.journal_entry.create_with_items(db, obj_in=entry_in)

def test_create_journal_entry_item_both_debit_credit_raises_error(db: Session, setup_basic_accounting_data):
    data = setup_basic_accounting_data
    items_in = [
        acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("100.00"), credit_amount=Decimal("50.00")),
        acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("50.00")),
    ]
    entry_in = acc_models.JournalEntryCreate(
        entry_date=date(2023,3,17), description="Test item both debit/credit", fiscal_year_id=data["fy"].id, items=items_in
    )
    with pytest.raises(ValueError, match="An item cannot have both debit and credit amounts"):
        acc_cruds.journal_entry.create_with_items(db, obj_in=entry_in)


def test_get_journal_items_for_account(db: Session, setup_basic_accounting_data):
    data = setup_basic_accounting_data
    # Entry 1
    acc_cruds.journal_entry.create_with_items(db, obj_in=acc_models.JournalEntryCreate(
        entry_date=date(2023, 4, 1), description="Cash Sale 1", fiscal_year_id=data["fy"].id,
        items=[
            acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("200.00")),
            acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("200.00"))
        ]
    ))
    # Entry 2
    acc_cruds.journal_entry.create_with_items(db, obj_in=acc_models.JournalEntryCreate(
        entry_date=date(2023, 4, 5), description="Office Expense Payment", fiscal_year_id=data["fy"].id,
        items=[
            acc_models.JournalItemCreate(account_id=data["expense"].id, debit_amount=Decimal("50.00")),
            acc_models.JournalItemCreate(account_id=data["cash"].id, credit_amount=Decimal("50.00"))
        ]
    ))

    cash_items = acc_cruds.journal_item.get_items_for_account(db, account_id=data["cash"].id)
    assert len(cash_items) == 2

    cash_debits = sum(item.debit_amount for item in cash_items)
    cash_credits = sum(item.credit_amount for item in cash_items)
    assert cash_debits == Decimal("200.00")
    assert cash_credits == Decimal("50.00")


# --- FinancialStatement CRUD Tests ---
def test_create_financial_statement(db: Session, setup_basic_accounting_data):
    data = setup_basic_accounting_data
    stmt_data = {"balance_sheet_items": [{"account": "Cash", "balance": "1000.00"}]}
    stmt_in = acc_models.FinancialStatementCreate(
        name="Balance Sheet Q1 2023",
        statement_type=acc_models.FinancialStatementTypeEnum.BALANCE_SHEET,
        fiscal_year_id=data["fy"].id,
        period_start_date=date(2023, 1, 1),
        period_end_date=date(2023, 3, 31),
        data_json=stmt_data
    )
    stmt = acc_cruds.financial_statement.create(db, obj_in=stmt_in)
    assert stmt is not None
    assert stmt.name == "Balance Sheet Q1 2023"
    assert stmt.data_json == stmt_data


# --- Trial Balance Report Test ---
def test_get_trial_balance(db: Session, setup_basic_accounting_data):
    data = setup_basic_accounting_data

    # Entry 1: Cash sale
    acc_cruds.journal_entry.create_with_items(db, obj_in=acc_models.JournalEntryCreate(
        entry_date=date(2023, 1, 10), description="Sale 1", fiscal_year_id=data["fy"].id,
        items=[
            acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("500.00")),
            acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("500.00"))
        ]
    ))
    # Entry 2: Paid expense
    acc_cruds.journal_entry.create_with_items(db, obj_in=acc_models.JournalEntryCreate(
        entry_date=date(2023, 1, 15), description="Expense 1", fiscal_year_id=data["fy"].id,
        items=[
            acc_models.JournalItemCreate(account_id=data["expense"].id, debit_amount=Decimal("75.00")),
            acc_models.JournalItemCreate(account_id=data["cash"].id, credit_amount=Decimal("75.00"))
        ]
    ))
    # Entry 3: Another cash sale
    acc_cruds.journal_entry.create_with_items(db, obj_in=acc_models.JournalEntryCreate(
        entry_date=date(2023, 1, 20), description="Sale 2", fiscal_year_id=data["fy"].id,
        items=[
            acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("300.00")),
            acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("300.00"))
        ]
    ))

    trial_balance = acc_cruds.get_trial_balance(db, fiscal_year_id=data["fy"].id, until_date=date(2023, 1, 31))

    assert len(trial_balance) == 3 # Cash, Revenue, Expense accounts were touched

    total_debits_report = sum(item['total_debit'] for item in trial_balance)
    total_credits_report = sum(item['total_credit'] for item in trial_balance)

    assert total_debits_report == Decimal("875.00") # 500 + 75 + 300
    assert total_credits_report == Decimal("875.00") # 500 + 75 + 300

    cash_row = next(item for item in trial_balance if item['account_code'] == data["cash"].code)
    revenue_row = next(item for item in trial_balance if item['account_code'] == data["revenue"].code)
    expense_row = next(item for item in trial_balance if item['account_code'] == data["expense"].code)

    assert cash_row['total_debit'] == Decimal("800.00") # 500 + 300
    assert cash_row['total_credit'] == Decimal("75.00")
    assert cash_row['balance'] == Decimal("725.00") # Debit balance for asset

    assert revenue_row['total_debit'] == Decimal("0.00")
    assert revenue_row['total_credit'] == Decimal("800.00") # 500 + 300
    assert revenue_row['balance'] == Decimal("800.00") # Credit balance for revenue (shown positive)

    assert expense_row['total_debit'] == Decimal("75.00")
    assert expense_row['total_credit'] == Decimal("0.00")
    assert expense_row['balance'] == Decimal("75.00") # Debit balance for expense
