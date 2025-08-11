import unittest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Generator, Dict, Any
from decimal import Decimal
from datetime import date

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# Adjust imports based on your project structure
from app.api.main import app
from app.api.dependencies import get_db_session
from app.accounting import models as acc_pydantic_models
from app.accounting import cruds as acc_cruds
from app.accounting.models import Base as AccountingBase
from app.api.models import Base as MainBase

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

class TestAccountingAPI(unittest.TestCase):
    def setUp(self):
        # Create all tables
        MainBase.metadata.create_all(bind=engine)
        self.client = TestClient(app)

    def tearDown(self):
        # Drop all tables after each test
        MainBase.metadata.drop_all(bind=engine)

    def create_default_fiscal_year(self) -> Dict[str, Any]:
        fy_data = {"name": "FY_API_Test", "start_date": "2023-01-01", "end_date": "2023-12-31"}
        response = self.client.post("/accounting/fiscal-years/", json=fy_data)
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_create_fiscal_year_api(self):
        fy_data = {"name": "FY2023_API", "start_date": "2023-01-01", "end_date": "2023-12-31", "status": "open"}
        response = self.client.post("/accounting/fiscal-years/", json=fy_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "FY2023_API")
        self.assertEqual(data["status"], "open")

    def test_read_fiscal_years_api(self):
        self.create_default_fiscal_year()
        response = self.client.get("/accounting/fiscal-years/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["name"], "FY_API_Test")

    def test_read_single_fiscal_year_api(self):
        created_fy = self.create_default_fiscal_year()
        fy_id = created_fy["id"]
        response = self.client.get(f"/accounting/fiscal-years/{fy_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], fy_id)
        self.assertEqual(data["name"], "FY_API_Test")

    def test_update_fiscal_year_api(self):
        created_fy = self.create_default_fiscal_year()
        fy_id = created_fy["id"]
        update_data = {"status": "closed", "is_closed_for_accounting": True}
        response = self.client.put(f"/accounting/fiscal-years/{fy_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "closed")
        self.assertTrue(data["is_closed_for_accounting"])

    def test_create_currency_api(self):
        currency_data = {"code": "TST", "name": "Test Currency", "symbol": "T"}
        response = self.client.post("/accounting/currencies/", json=currency_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["code"], "TST")
        self.assertEqual(data["name"], "Test Currency")

    def test_create_chart_of_account_api(self):
        account_data = {"code": "9999", "name": "API Test Account", "account_type": "asset"}
        response = self.client.post("/accounting/chart-of-accounts/", json=account_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["code"], "9999")
        self.assertEqual(data["name"], "API Test Account")
        self.assertEqual(data["account_type"], "asset")

    def test_create_chart_of_account_with_parent_api(self):
        parent_data = {"code": "8000", "name": "API Parent", "account_type": "liability"}
        parent_response = self.client.post("/accounting/chart-of-accounts/", json=parent_data)
        self.assertEqual(parent_response.status_code, 201)
        parent_id = parent_response.json()["id"]

        child_data = {"code": "8001", "name": "API Child", "account_type": "liability", "parent_id": parent_id}
        child_response = self.client.post("/accounting/chart-of-accounts/", json=child_data)
        self.assertEqual(child_response.status_code, 201)
        data = child_response.json()
        self.assertEqual(data["parent_id"], parent_id)

    def setup_accounts_for_journal_entry_api(self) -> Dict[str, str]:
        fy = self.create_default_fiscal_year()

        cash_data = {"code": "1010A", "name": "Cash API", "account_type": "asset"}
        cash_resp = self.client.post("/accounting/chart-of-accounts/", json=cash_data)
        self.assertEqual(cash_resp.status_code, 201)

        revenue_data = {"code": "4010A", "name": "Revenue API", "account_type": "revenue"}
        rev_resp = self.client.post("/accounting/chart-of-accounts/", json=revenue_data)
        self.assertEqual(rev_resp.status_code, 201)

        return {
            "fiscal_year_id": fy["id"],
            "cash_account_id": cash_resp.json()["id"],
            "revenue_account_id": rev_resp.json()["id"]
        }

    def test_create_journal_entry_api_balanced(self):
        acc_ids = self.setup_accounts_for_journal_entry_api()
        entry_data = {
            "entry_date": "2023-07-01",
            "description": "API Test Entry - Balanced",
            "fiscal_year_id": acc_ids["fiscal_year_id"],
            "items": [
                {"account_id": acc_ids["cash_account_id"], "debit_amount": "150.00", "credit_amount": "0.00"},
                {"account_id": acc_ids["revenue_account_id"], "debit_amount": "0.00", "credit_amount": "150.00"}
            ]
        }
        response = self.client.post("/accounting/journal-entries/", json=entry_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["description"], "API Test Entry - Balanced")
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(data["items"][0]["debit_amount"], "150.00")
        self.assertEqual(data["items"][1]["credit_amount"], "150.00")

    def test_create_journal_entry_api_unbalanced(self):
        acc_ids = self.setup_accounts_for_journal_entry_api()
        entry_data = {
            "entry_date": "2023-07-02",
            "description": "API Test Entry - Unbalanced",
            "fiscal_year_id": acc_ids["fiscal_year_id"],
            "items": [
                {"account_id": acc_ids["cash_account_id"], "debit_amount": "150.00"},
                {"account_id": acc_ids["revenue_account_id"], "credit_amount": "140.00"}
            ]
        }
        response = self.client.post("/accounting/journal-entries/", json=entry_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Total debits must equal total credits", response.json()["detail"])

    def test_create_journal_entry_api_inactive_account(self):
        acc_ids = self.setup_accounts_for_journal_entry_api()

        # Deactivate one account
        self.client.put(f"/accounting/chart-of-accounts/{acc_ids['cash_account_id']}", json={"is_active": False})

        entry_data = {
            "entry_date": "2023-07-03",
            "description": "API Test Entry - Inactive Account",
            "fiscal_year_id": acc_ids["fiscal_year_id"],
            "items": [
                {"account_id": acc_ids["cash_account_id"], "debit_amount": "50.00"},
                {"account_id": acc_ids["revenue_account_id"], "credit_amount": "50.00"}
            ]
        }
        response = self.client.post("/accounting/journal-entries/", json=entry_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("is not active", response.json()["detail"])

    def test_get_trial_balance_report_api(self):
        acc_ids = self.setup_accounts_for_journal_entry_api()

        # Post a balanced journal entry
        entry_data = {
            "entry_date": "2023-08-01", "description": "Report Test Entry", "fiscal_year_id": acc_ids["fiscal_year_id"],
            "items": [
                {"account_id": acc_ids["cash_account_id"], "debit_amount": "1000.50"},
                {"account_id": acc_ids["revenue_account_id"], "credit_amount": "1000.50"}
            ]
        }
        self.client.post("/accounting/journal-entries/", json=entry_data)

        report_params = {
            "fiscal_year_id": acc_ids["fiscal_year_id"],
            "until_date": "2023-12-31"
        }
        response = self.client.get("/accounting/reports/trial-balance/", params=report_params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        total_debits_report = sum(Decimal(item.get('total_debit', "0")) for item in data)
        total_credits_report = sum(Decimal(item.get('total_credit', "0")) for item in data)
        self.assertEqual(total_debits_report, total_credits_report)
        self.assertEqual(total_debits_report, Decimal("1000.50"))

        cash_row = next(item for item in data if item['account_code'] == "1010A")
        self.assertEqual(Decimal(cash_row['balance']), Decimal("1000.50"))

    def test_read_non_existent_fiscal_year_api(self):
        response = self.client.get("/accounting/fiscal-years/non_existent_uuid")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Fiscal year not found", response.json()["detail"])
