import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if needed for fixtures
from typing import Generator, Dict, Any
from decimal import Decimal
from datetime import date

# Adjust imports based on your project structure
from api.main import app # Your FastAPI app instance
from api.dependencies import get_db_session # To override dependency
from accounting import models as acc_pydantic_models # Pydantic models for request/response
from accounting import cruds as acc_cruds # For direct data manipulation or verification if needed
from accounting.models import Base as AccountingBase # SQLAlchemy Base for accounting tables
from api.models import Base as MainBase # Main SQLAlchemy Base if different and used by accounting

# Use the same in-memory SQLite setup as in test_cruds.py
from .test_cruds import SQLALCHEMY_DATABASE_URL, TestingSessionLocal, engine

# Override the get_db_session dependency for testing
def override_get_db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db_session] = override_get_db_session

@pytest.fixture(scope="function", autouse=True) # autouse ensures this runs for every test
def setup_database():
    # Create all tables. This needs to include all tables your app might touch,
    # or at least those relevant to the accounting module.
    # If accounting uses a separate Base: AccountingBase.metadata.create_all(bind=engine)
    MainBase.metadata.create_all(bind=engine) # Creates all tables known to MainBase.
                                             # Ensure accounting tables are registered with this.
    yield
    # Drop all tables after each test
    MainBase.metadata.drop_all(bind=engine)
    # If accounting uses a separate Base: AccountingBase.metadata.drop_all(bind=engine)


client = TestClient(app)

# --- Helper to create a fiscal year for other tests ---
def create_default_fiscal_year() -> Dict[str, Any]:
    fy_data = {"name": "FY_API_Test", "start_date": "2023-01-01", "end_date": "2023-12-31"}
    response = client.post("/accounting/fiscal-years/", json=fy_data)
    assert response.status_code == 201
    return response.json()

# --- FiscalYear API Tests ---
def test_create_fiscal_year_api():
    fy_data = {"name": "FY2023_API", "start_date": "2023-01-01", "end_date": "2023-12-31", "status": "open"}
    response = client.post("/accounting/fiscal-years/", json=fy_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "FY2023_API"
    assert data["status"] == "open"

def test_read_fiscal_years_api():
    create_default_fiscal_year()
    response = client.get("/accounting/fiscal-years/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "FY_API_Test"

def test_read_single_fiscal_year_api():
    created_fy = create_default_fiscal_year()
    fy_id = created_fy["id"]
    response = client.get(f"/accounting/fiscal-years/{fy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fy_id
    assert data["name"] == "FY_API_Test"

def test_update_fiscal_year_api():
    created_fy = create_default_fiscal_year()
    fy_id = created_fy["id"]
    update_data = {"status": "closed", "is_closed_for_accounting": True}
    response = client.put(f"/accounting/fiscal-years/{fy_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "closed"
    assert data["is_closed_for_accounting"] is True


# --- Currency API Tests ---
def test_create_currency_api():
    currency_data = {"code": "TST", "name": "Test Currency", "symbol": "T"}
    response = client.post("/accounting/currencies/", json=currency_data)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "TST"
    assert data["name"] == "Test Currency"

# --- ChartOfAccounts API Tests ---
def test_create_chart_of_account_api():
    account_data = {"code": "9999", "name": "API Test Account", "account_type": "asset"}
    response = client.post("/accounting/chart-of-accounts/", json=account_data)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "9999"
    assert data["name"] == "API Test Account"
    assert data["account_type"] == "asset"

def test_create_chart_of_account_with_parent_api():
    parent_data = {"code": "8000", "name": "API Parent", "account_type": "liability"}
    parent_response = client.post("/accounting/chart-of-accounts/", json=parent_data)
    assert parent_response.status_code == 201
    parent_id = parent_response.json()["id"]

    child_data = {"code": "8001", "name": "API Child", "account_type": "liability", "parent_id": parent_id}
    child_response = client.post("/accounting/chart-of-accounts/", json=child_data)
    assert child_response.status_code == 201
    data = child_response.json()
    assert data["parent_id"] == parent_id


# --- JournalEntry API Tests ---
@pytest.fixture
def setup_accounts_for_journal_entry_api() -> Dict[str, str]:
    fy = create_default_fiscal_year()

    cash_data = {"code": "1010A", "name": "Cash API", "account_type": "asset"}
    cash_resp = client.post("/accounting/chart-of-accounts/", json=cash_data)
    assert cash_resp.status_code == 201

    revenue_data = {"code": "4010A", "name": "Revenue API", "account_type": "revenue"}
    rev_resp = client.post("/accounting/chart-of-accounts/", json=revenue_data)
    assert rev_resp.status_code == 201

    return {
        "fiscal_year_id": fy["id"],
        "cash_account_id": cash_resp.json()["id"],
        "revenue_account_id": rev_resp.json()["id"]
    }

def test_create_journal_entry_api_balanced(setup_accounts_for_journal_entry_api):
    acc_ids = setup_accounts_for_journal_entry_api
    entry_data = {
        "entry_date": "2023-07-01",
        "description": "API Test Entry - Balanced",
        "fiscal_year_id": acc_ids["fiscal_year_id"],
        "items": [
            {"account_id": acc_ids["cash_account_id"], "debit_amount": "150.00", "credit_amount": "0.00"},
            {"account_id": acc_ids["revenue_account_id"], "debit_amount": "0.00", "credit_amount": "150.00"}
        ]
    }
    response = client.post("/accounting/journal-entries/", json=entry_data)
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "API Test Entry - Balanced"
    assert len(data["items"]) == 2
    # Pydantic should convert "150.00" string to Decimal for CRUD, then back to string for JSON
    assert data["items"][0]["debit_amount"] == "150.00"
    assert data["items"][1]["credit_amount"] == "150.00"


def test_create_journal_entry_api_unbalanced(setup_accounts_for_journal_entry_api):
    acc_ids = setup_accounts_for_journal_entry_api
    entry_data = {
        "entry_date": "2023-07-02",
        "description": "API Test Entry - Unbalanced",
        "fiscal_year_id": acc_ids["fiscal_year_id"],
        "items": [
            {"account_id": acc_ids["cash_account_id"], "debit_amount": "150.00"}, # Credit is 0 by default
            {"account_id": acc_ids["revenue_account_id"], "credit_amount": "140.00"} # Debit is 0 by default
        ]
    }
    response = client.post("/accounting/journal-entries/", json=entry_data)
    assert response.status_code == 400 # Due to CRUD validation
    assert "Total debits must equal total credits" in response.json()["detail"]

def test_create_journal_entry_api_inactive_account(setup_accounts_for_journal_entry_api):
    acc_ids = setup_accounts_for_journal_entry_api

    # Deactivate one account
    client.put(f"/accounting/chart-of-accounts/{acc_ids['cash_account_id']}", json={"is_active": False})

    entry_data = {
        "entry_date": "2023-07-03",
        "description": "API Test Entry - Inactive Account",
        "fiscal_year_id": acc_ids["fiscal_year_id"],
        "items": [
            {"account_id": acc_ids["cash_account_id"], "debit_amount": "50.00"},
            {"account_id": acc_ids["revenue_account_id"], "credit_amount": "50.00"}
        ]
    }
    response = client.post("/accounting/journal-entries/", json=entry_data)
    assert response.status_code == 400
    assert "is not active" in response.json()["detail"]


# --- Trial Balance Report API Test ---
def test_get_trial_balance_report_api(setup_accounts_for_journal_entry_api):
    acc_ids = setup_accounts_for_journal_entry_api

    # Post a balanced journal entry
    entry_data = {
        "entry_date": "2023-08-01", "description": "Report Test Entry", "fiscal_year_id": acc_ids["fiscal_year_id"],
        "items": [
            {"account_id": acc_ids["cash_account_id"], "debit_amount": "1000.50"},
            {"account_id": acc_ids["revenue_account_id"], "credit_amount": "1000.50"}
        ]
    }
    client.post("/accounting/journal-entries/", json=entry_data)

    report_params = {
        "fiscal_year_id": acc_ids["fiscal_year_id"],
        "until_date": "2023-12-31"
    }
    response = client.get("/accounting/reports/trial-balance/", params=report_params)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Should have at least cash and revenue accounts

    total_debits_report = sum(Decimal(item.get('total_debit', "0")) for item in data)
    total_credits_report = sum(Decimal(item.get('total_credit', "0")) for item in data)
    assert total_debits_report == total_credits_report
    assert total_debits_report == Decimal("1000.50")

    cash_row = next(item for item in data if item['account_code'] == "1010A") # Code from fixture
    assert Decimal(cash_row['balance']) == Decimal("1000.50")

# More tests:
# - Reading specific journal entries
# - Updating journal entry headers (not items, as that's complex)
# - Error handling for non-existent IDs (accounts, fiscal years) in POST/PUT requests
# - Pagination and more detailed filtering for GET list endpoints
# - Tax Rates API tests
# - Financial Statements API tests (create record, read record)

# Example of testing a non-existent resource
def test_read_non_existent_fiscal_year_api():
    response = client.get("/accounting/fiscal-years/non_existent_uuid")
    assert response.status_code == 404
    assert "Fiscal year not found" in response.json()["detail"]
