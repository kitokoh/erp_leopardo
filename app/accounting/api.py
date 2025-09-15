from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from decimal import Decimal
from datetime import date

from . import cruds, models # models here refers to Pydantic models from accounting.models
from app.db.session_manager import get_db as get_db_session # Assuming a general DB session dependency

router = APIRouter(
    prefix="/accounting",
    tags=["Accounting"],
    responses={404: {"description": "Not found"}},
)

# --- Fiscal Year Endpoints ---
@router.post("/fiscal-years/", response_model=models.FiscalYearRead, status_code=201)
def create_fiscal_year(
    *,
    db: Session = Depends(get_db_session),
    fiscal_year_in: models.FiscalYearCreate
):
    existing_fiscal_year = cruds.fiscal_year.get_by_name(db, name=fiscal_year_in.name)
    if existing_fiscal_year:
        raise HTTPException(status_code=400, detail="Fiscal year with this name already exists.")
    # Add more validation for start/end dates if needed (e.g., end_date > start_date)
    return cruds.fiscal_year.create(db=db, obj_in=fiscal_year_in)

@router.get("/fiscal-years/", response_model=List[models.FiscalYearRead])
def read_fiscal_years(
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100
):
    return cruds.fiscal_year.get_multi(db, skip=skip, limit=limit)

@router.get("/fiscal-years/{fiscal_year_id}", response_model=models.FiscalYearRead)
def read_fiscal_year(
    *,
    db: Session = Depends(get_db_session),
    fiscal_year_id: str
):
    db_fiscal_year = cruds.fiscal_year.get(db, id=fiscal_year_id)
    if not db_fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return db_fiscal_year

@router.put("/fiscal-years/{fiscal_year_id}", response_model=models.FiscalYearRead)
def update_fiscal_year(
    *,
    db: Session = Depends(get_db_session),
    fiscal_year_id: str,
    fiscal_year_in: models.FiscalYearUpdate
):
    db_fiscal_year = cruds.fiscal_year.get(db, id=fiscal_year_id)
    if not db_fiscal_year:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    return cruds.fiscal_year.update(db=db, db_obj=db_fiscal_year, obj_in=fiscal_year_in)

# --- Currency Endpoints ---
@router.post("/currencies/", response_model=models.CurrencyRead, status_code=201)
def create_currency(
    *,
    db: Session = Depends(get_db_session),
    currency_in: models.CurrencyCreate
):
    existing_currency = cruds.currency.get(db, id=currency_in.code)
    if existing_currency:
        raise HTTPException(status_code=400, detail=f"Currency with code {currency_in.code} already exists.")
    return cruds.currency.create(db=db, obj_in=currency_in)

@router.get("/currencies/", response_model=List[models.CurrencyRead])
def read_currencies(
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100
):
    return cruds.currency.get_multi(db, skip=skip, limit=limit)

@router.get("/currencies/{currency_code}", response_model=models.CurrencyRead)
def read_currency(
    *,
    db: Session = Depends(get_db_session),
    currency_code: str
):
    db_currency = cruds.currency.get(db, id=currency_code)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return db_currency

@router.put("/currencies/{currency_code}", response_model=models.CurrencyRead)
def update_currency(
    *,
    db: Session = Depends(get_db_session),
    currency_code: str,
    currency_in: models.CurrencyUpdate
):
    db_currency = cruds.currency.get(db, id=currency_code)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return cruds.currency.update(db=db, db_obj=db_currency, obj_in=currency_in)

@router.patch("/currencies/{currency_code}/set-base", response_model=models.CurrencyRead)
def set_base_currency(
    *,
    db: Session = Depends(get_db_session),
    currency_code: str
):
    updated_currency = cruds.currency.set_base_currency(db, currency_code=currency_code)
    if not updated_currency:
        raise HTTPException(status_code=404, detail=f"Currency with code {currency_code} not found.")
    return updated_currency

# --- TaxRate Endpoints ---
@router.post("/tax-rates/", response_model=models.TaxRateRead, status_code=201)
def create_tax_rate(
    *,
    db: Session = Depends(get_db_session),
    tax_rate_in: models.TaxRateCreate
):
    existing = cruds.tax_rate.get_by_name(db, name=tax_rate_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="Tax rate with this name already exists.")
    return cruds.tax_rate.create(db=db, obj_in=tax_rate_in)

@router.get("/tax-rates/", response_model=List[models.TaxRateRead])
def read_tax_rates(
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
):
    # Note: CRUDBase.get_multi doesn't support filtering by default.
    # This would require extending CRUDBase or adding custom logic in CRUDTaxRate.
    # For now, returning all and letting client filter, or implement filtering in CRUD layer.
    items = cruds.tax_rate.get_multi(db, skip=skip, limit=limit)
    if is_active is not None:
        items = [item for item in items if item.is_active == is_active]
    return items


@router.get("/tax-rates/{tax_rate_id}", response_model=models.TaxRateRead)
def read_tax_rate(
    *,
    db: Session = Depends(get_db_session),
    tax_rate_id: str
):
    db_tax_rate = cruds.tax_rate.get(db, id=tax_rate_id)
    if not db_tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return db_tax_rate

@router.put("/tax-rates/{tax_rate_id}", response_model=models.TaxRateRead)
def update_tax_rate(
    *,
    db: Session = Depends(get_db_session),
    tax_rate_id: str,
    tax_rate_in: models.TaxRateUpdate
):
    db_tax_rate = cruds.tax_rate.get(db, id=tax_rate_id)
    if not db_tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return cruds.tax_rate.update(db=db, db_obj=db_tax_rate, obj_in=tax_rate_in)


# --- Chart of Accounts Endpoints ---
@router.post("/chart-of-accounts/", response_model=models.ChartOfAccountsRead, status_code=201)
def create_account(
    *,
    db: Session = Depends(get_db_session),
    account_in: models.ChartOfAccountsCreate
):
    existing_account = cruds.chart_of_accounts.get_by_code(db, code=account_in.code)
    if existing_account:
        raise HTTPException(status_code=400, detail=f"Account with code {account_in.code} already exists.")
    if account_in.parent_id:
        parent_account = cruds.chart_of_accounts.get(db, id=account_in.parent_id)
        if not parent_account:
            raise HTTPException(status_code=404, detail=f"Parent account with id {account_in.parent_id} not found.")
    return cruds.chart_of_accounts.create(db=db, obj_in=account_in)

@router.get("/chart-of-accounts/", response_model=List[models.ChartOfAccountsRead])
def read_accounts(
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    account_type: Optional[models.AccountTypeEnum] = None,
    is_active: Optional[bool] = None,
    parent_id: Optional[str] = Query(None, description="Filter by parent account ID. Use 'null' for top-level accounts.")
):
    # This is a simplified version. Real filtering should be done at DB level via CRUD.
    accounts = cruds.chart_of_accounts.get_multi(db, skip=skip, limit=limit)
    if account_type:
        accounts = [acc for acc in accounts if acc.account_type == account_type]
    if is_active is not None:
        accounts = [acc for acc in accounts if acc.is_active == is_active]
    if parent_id:
        if parent_id.lower() == "null":
            accounts = [acc for acc in accounts if acc.parent_id is None]
        else:
            accounts = [acc for acc in accounts if acc.parent_id == parent_id]
    return accounts


@router.get("/chart-of-accounts/{account_id}", response_model=models.ChartOfAccountsRead)
def read_account(
    *,
    db: Session = Depends(get_db_session),
    account_id: str
):
    db_account = cruds.chart_of_accounts.get(db, id=account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account

@router.put("/chart-of-accounts/{account_id}", response_model=models.ChartOfAccountsRead)
def update_account(
    *,
    db: Session = Depends(get_db_session),
    account_id: str,
    account_in: models.ChartOfAccountsUpdate
):
    db_account = cruds.chart_of_accounts.get(db, id=account_id)
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account_in.parent_id and account_in.parent_id == account_id: # Prevent self-referencing
        raise HTTPException(status_code=400, detail="Account cannot be its own parent.")
    if account_in.parent_id:
        parent_account = cruds.chart_of_accounts.get(db, id=account_in.parent_id)
        if not parent_account:
            raise HTTPException(status_code=404, detail=f"Parent account with id {account_in.parent_id} not found.")
    return cruds.chart_of_accounts.update(db=db, db_obj=db_account, obj_in=account_in)


# --- Journal Entry Endpoints ---
@router.post("/journal-entries/", response_model=models.JournalEntryRead, status_code=201)
def create_journal_entry(
    *,
    db: Session = Depends(get_db_session),
    entry_in: models.JournalEntryCreate
):
    # Ensure fiscal year exists
    fiscal_year = cruds.fiscal_year.get(db, id=entry_in.fiscal_year_id)
    if not fiscal_year:
        raise HTTPException(status_code=404, detail=f"Fiscal year with id {entry_in.fiscal_year_id} not found.")
    if fiscal_year.is_closed_for_accounting:
        raise HTTPException(status_code=400, detail=f"Fiscal year {fiscal_year.name} is closed.")

    # Ensure all accounts in items exist
    for item_create in entry_in.items:
        account = cruds.chart_of_accounts.get(db, id=item_create.account_id)
        if not account:
            raise HTTPException(status_code=404, detail=f"Account with id {item_create.account_id} not found.")
        if not account.is_active:
            raise HTTPException(status_code=400, detail=f"Account {account.code} ({account.name}) is not active.")

    try:
        return cruds.journal_entry.create_with_items(db=db, obj_in=entry_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/journal-entries/", response_model=List[models.JournalEntryRead])
def read_journal_entries(
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    fiscal_year_id: Optional[str] = None
):
    # This is a simplified listing. Advanced filtering should be in CRUD.
    if start_date and end_date:
        return cruds.journal_entry.get_entries_for_period(db, start_date=start_date, end_date=end_date)

    entries = cruds.journal_entry.get_multi(db, skip=skip, limit=limit)
    if fiscal_year_id:
        entries = [e for e in entries if e.fiscal_year_id == fiscal_year_id]
    return entries


@router.get("/journal-entries/{entry_id}", response_model=models.JournalEntryRead)
def read_journal_entry(
    *,
    db: Session = Depends(get_db_session),
    entry_id: str
):
    db_entry = cruds.journal_entry.get(db, id=entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return db_entry

# Updating journal entries can be complex (especially items).
# Often, entries are reversed and re-entered rather than directly updated.
# A full PUT/PATCH might involve deleting old items and creating new ones.
# For now, a simple update for top-level fields.
@router.put("/journal-entries/{entry_id}", response_model=models.JournalEntryRead)
def update_journal_entry_details(
    *,
    db: Session = Depends(get_db_session),
    entry_id: str,
    entry_in: models.JournalEntryUpdate # This Pydantic model should NOT include items for this endpoint
):
    db_entry = cruds.journal_entry.get(db, id=entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Check if fiscal year is closed if trying to change date or fiscal year
    if entry_in.fiscal_year_id and entry_in.fiscal_year_id != db_entry.fiscal_year_id:
        new_fy = cruds.fiscal_year.get(db, id=entry_in.fiscal_year_id)
        if not new_fy: raise HTTPException(status_code=404, detail="New fiscal year not found.")
        if new_fy.is_closed_for_accounting: raise HTTPException(status_code=400, detail="New fiscal year is closed.")

    if db_entry.fiscal_year.is_closed_for_accounting and \
       (entry_in.entry_date and entry_in.entry_date != db_entry.entry_date):
        raise HTTPException(status_code=400, detail="Cannot change date of an entry in a closed fiscal year.")

    return cruds.journal_entry.update(db=db, db_obj=db_entry, obj_in=entry_in)


# --- Financial Statement Endpoints ---
# Financial statements are typically generated, not created directly via POST in the same way.
# GET endpoint for a specific statement might be more common.
@router.post("/financial-statements/", response_model=models.FinancialStatementRead, status_code=201)
def create_financial_statement_record( # This is for storing an already generated statement
    *,
    db: Session = Depends(get_db_session),
    statement_in: models.FinancialStatementCreate
):
    # Check fiscal year
    fy = cruds.fiscal_year.get(db, id=statement_in.fiscal_year_id)
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found.")
    # Further validation: statement period should be within fiscal year, etc.
    return cruds.financial_statement.create(db=db, obj_in=statement_in)


@router.get("/financial-statements/{statement_id}", response_model=models.FinancialStatementRead)
def read_financial_statement(
    *,
    db: Session = Depends(get_db_session),
    statement_id: str
):
    db_statement = cruds.financial_statement.get(db, id=statement_id)
    if not db_statement:
        raise HTTPException(status_code=404, detail="Financial statement not found")
    return db_statement

@router.get("/financial-statements/", response_model=List[models.FinancialStatementRead])
def list_financial_statements(
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100,
    statement_type: Optional[models.FinancialStatementTypeEnum] = None,
    fiscal_year_id: Optional[str] = None
):
    # Simplified listing, extend CRUD for proper filtering
    statements = cruds.financial_statement.get_multi(db, skip=skip, limit=limit)
    if statement_type:
        statements = [s for s in statements if s.statement_type == statement_type]
    if fiscal_year_id:
        statements = [s for s in statements if s.fiscal_year_id == fiscal_year_id]
    return statements


# --- Reporting Endpoints ---
@router.get("/reports/trial-balance/", response_model=List[Dict[str, Any]]) # Adjust response model as needed
def get_trial_balance_report(
    *,
    db: Session = Depends(get_db_session),
    fiscal_year_id: str,
    until_date: date
):
    fy = cruds.fiscal_year.get(db, id=fiscal_year_id)
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found.")
    if until_date < fy.start_date or until_date > fy.end_date:
        raise HTTPException(status_code=400, detail=f"Report date {until_date} is outside fiscal year {fy.name} ({fy.start_date} - {fy.end_date}).")

    trial_balance_data = cruds.get_trial_balance(db, fiscal_year_id=fiscal_year_id, until_date=until_date)

    # Check for balance
    total_debits = sum(item.get('total_debit', Decimal(0)) for item in trial_balance_data)
    total_credits = sum(item.get('total_credit', Decimal(0)) for item in trial_balance_data)

    if total_debits != total_credits:
        # This indicates an issue with underlying data or journal entries
        # Log this server-side. May or may not raise HTTP error depending on policy.
        print(f"WARNING: Trial balance for FY {fiscal_year_id} until {until_date} is NOT balanced. Debits: {total_debits}, Credits: {total_credits}")
        # For strictness, one might raise an error:
        # raise HTTPException(status_code=500, detail="Trial balance is not balanced. Check journal entries.")

    return trial_balance_data

# Add other report endpoints (Balance Sheet, P&L) here.
# These will require more complex logic within their respective CRUD/service functions.
# For example:
# @router.get("/reports/balance-sheet/")
# def get_balance_sheet_report(...): ...
#
# @router.get("/reports/profit-and-loss/")
# def get_profit_and_loss_report(...): ...
