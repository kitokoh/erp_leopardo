import unittest
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
from accounting import models
from accounting import cruds as acc_cruds
from api.models import Base as MainBase # The Base used by accounting models if it's shared

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestAccountingCruds(unittest.TestCase):
    def setUp(self):
        MainBase.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()
        MainBase.metadata.drop_all(bind=engine)

    def test_create_fiscal_year(self):
        fy_in = acc_models.FiscalYearCreate(name="FY2023", start_date=date(2023, 1, 1), end_date=date(2023, 12, 31))
        fy = acc_cruds.fiscal_year.create(self.db, obj_in=fy_in)
        self.assertIsNotNone(fy)
        self.assertEqual(fy.name, "FY2023")
        self.assertEqual(fy.start_date, date(2023, 1, 1))
        self.assertEqual(fy.status, acc_models.FiscalYearStatusEnum.OPEN)

    def test_get_fiscal_year(self):
        fy_in = acc_models.FiscalYearCreate(name="FY2024", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        created_fy = acc_cruds.fiscal_year.create(self.db, obj_in=fy_in)

        retrieved_fy = acc_cruds.fiscal_year.get(self.db, id=created_fy.id)
        self.assertIsNotNone(retrieved_fy)
        self.assertEqual(retrieved_fy.id, created_fy.id)
        self.assertEqual(retrieved_fy.name, "FY2024")

    def test_get_fiscal_year_by_name(self):
        fy_in = acc_models.FiscalYearCreate(name="FY2025_Test", start_date=date(2025,1,1), end_date=date(2025,12,31))
        acc_cruds.fiscal_year.create(self.db, obj_in=fy_in)
        retrieved_fy = acc_cruds.fiscal_year.get_by_name(self.db, name="FY2025_Test")
        self.assertIsNotNone(retrieved_fy)
        self.assertEqual(retrieved_fy.name, "FY2025_Test")

    def test_get_fiscal_year_by_date(self):
        fy_in = acc_models.FiscalYearCreate(name="FY_DateTest", start_date=date(2023, 6, 1), end_date=date(2024, 5, 31))
        acc_cruds.fiscal_year.create(self.db, obj_in=fy_in)
        target_date = date(2023, 10, 15)
        retrieved_fy = acc_cruds.fiscal_year.get_by_date(self.db, target_date=target_date)
        self.assertIsNotNone(retrieved_fy)
        self.assertEqual(retrieved_fy.name, "FY_DateTest")
        self.assertLessEqual(retrieved_fy.start_date, target_date)
        self.assertGreaterEqual(retrieved_fy.end_date, target_date)

    def test_update_fiscal_year(self):
        fy_in = acc_models.FiscalYearCreate(name="FY_Update", start_date=date(2023,1,1), end_date=date(2023,12,31))
        created_fy = acc_cruds.fiscal_year.create(self.db, obj_in=fy_in)

        update_data = acc_models.FiscalYearUpdate(status=acc_models.FiscalYearStatusEnum.CLOSED, is_closed_for_accounting=True)
        updated_fy = acc_cruds.fiscal_year.update(self.db, db_obj=created_fy, obj_in=update_data)

        self.assertEqual(updated_fy.status, acc_models.FiscalYearStatusEnum.CLOSED)
        self.assertTrue(updated_fy.is_closed_for_accounting)
        self.assertEqual(updated_fy.name, "FY_Update")

    def test_create_currency(self):
        currency_in = acc_models.CurrencyCreate(code="EUR", name="Euro", symbol="€", exchange_rate_to_base=Decimal("0.92"))
        curr = acc_cruds.currency.create(self.db, obj_in=currency_in)
        self.assertIsNotNone(curr)
        self.assertEqual(curr.code, "EUR")
        self.assertEqual(curr.name, "Euro")

    def test_get_currency(self):
        currency_in = acc_models.CurrencyCreate(code="GBP", name="British Pound", symbol="£")
        acc_cruds.currency.create(self.db, obj_in=currency_in)
        retrieved_curr = acc_cruds.currency.get(self.db, id="GBP")
        self.assertIsNotNone(retrieved_curr)
        self.assertEqual(retrieved_curr.code, "GBP")

    def test_set_base_currency(self):
        acc_cruds.currency.create(self.db, obj_in=acc_models.CurrencyCreate(code="USD", name="US Dollar", is_base_currency=False))
        acc_cruds.currency.create(self.db, obj_in=acc_models.CurrencyCreate(code="CAD", name="Canadian Dollar", is_base_currency=False))

        acc_cruds.currency.set_base_currency(self.db, currency_code="CAD")
        base_curr = acc_cruds.currency.get_base_currency(self.db)
        self.assertIsNotNone(base_curr)
        self.assertEqual(base_curr.code, "CAD")

        usd_curr = acc_cruds.currency.get(self.db, id="USD")
        self.assertIsNotNone(usd_curr)
        self.assertFalse(usd_curr.is_base_currency)

    def test_create_tax_rate(self):
        tax_in = acc_models.TaxRateCreate(name="VAT 20%", rate_percentage=Decimal("20.00"), tax_type=acc_models.TaxTypeEnum.VAT)
        tax = acc_cruds.tax_rate.create(self.db, obj_in=tax_in)
        self.assertIsNotNone(tax)
        self.assertEqual(tax.name, "VAT 20%")
        self.assertEqual(tax.rate_percentage, Decimal("20.00"))

    def test_create_chart_of_account(self):
        acc_in = acc_models.ChartOfAccountsCreate(code="10100", name="Cash", account_type=acc_models.AccountTypeEnum.ASSET)
        acc = acc_cruds.chart_of_accounts.create(self.db, obj_in=acc_in)
        self.assertIsNotNone(acc)
        self.assertEqual(acc.code, "10100")
        self.assertEqual(acc.name, "Cash")

    def test_create_child_account(self):
        parent_in = acc_models.ChartOfAccountsCreate(code="10000", name="Assets", account_type=acc_models.AccountTypeEnum.ASSET)
        parent_acc = acc_cruds.chart_of_accounts.create(self.db, obj_in=parent_in)

        child_in = acc_models.ChartOfAccountsCreate(code="10100", name="Cash", account_type=acc_models.AccountTypeEnum.ASSET, parent_id=parent_acc.id)
        child_acc = acc_cruds.chart_of_accounts.create(self.db, obj_in=child_in)

        self.assertIsNotNone(child_acc)
        self.assertEqual(child_acc.parent_id, parent_acc.id)
        retrieved_parent = self.db.query(acc_models.ChartOfAccounts).filter(acc_models.ChartOfAccounts.id == parent_acc.id).one()
        self.assertIn(child_acc, retrieved_parent.children)

    def setup_basic_accounting_data(self):
        fy = acc_cruds.fiscal_year.create(self.db, obj_in=acc_models.FiscalYearCreate(name="FY_JournalTest", start_date=date(2023,1,1), end_date=date(2023,12,31)))
        cash_acc = acc_cruds.chart_of_accounts.create(self.db, obj_in=acc_models.ChartOfAccountsCreate(code="1010", name="Cash", account_type=acc_models.AccountTypeEnum.ASSET))
        revenue_acc = acc_cruds.chart_of_accounts.create(self.db, obj_in=acc_models.ChartOfAccountsCreate(code="4010", name="Sales Revenue", account_type=acc_models.AccountTypeEnum.REVENUE))
        expense_acc = acc_cruds.chart_of_accounts.create(self.db, obj_in=acc_models.ChartOfAccountsCreate(code="5010", name="Office Expense", account_type=acc_models.AccountTypeEnum.EXPENSE))
        return {"fy": fy, "cash": cash_acc, "revenue": revenue_acc, "expense": expense_acc}

    def test_create_journal_entry_with_items_balanced(self):
        data = self.setup_basic_accounting_data()
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

        created_entry = acc_cruds.journal_entry.create_with_items(self.db, obj_in=entry_in)
        self.assertIsNotNone(created_entry)
        self.assertEqual(created_entry.description, "Received payment for services")
        self.assertEqual(len(created_entry.items), 2)

        retrieved_items = sorted(created_entry.items, key=lambda x: x.account_id)
        cash_item = next(i for i in retrieved_items if i.account_id == data["cash"].id)
        revenue_item = next(i for i in retrieved_items if i.account_id == data["revenue"].id)

        self.assertEqual(cash_item.debit_amount, Decimal("100.00"))
        self.assertEqual(cash_item.credit_amount, Decimal("0.00"))
        self.assertEqual(revenue_item.credit_amount, Decimal("100.00"))
        self.assertEqual(revenue_item.debit_amount, Decimal("0.00"))

    def test_create_journal_entry_unbalanced_raises_error(self):
        data = self.setup_basic_accounting_data()
        items_in = [
            acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("100.00")),
            acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("90.00")),
        ]
        entry_in = acc_models.JournalEntryCreate(
            entry_date=date(2023,3,16), description="Test unbalanced", fiscal_year_id=data["fy"].id, items=items_in
        )
        with self.assertRaisesRegex(ValueError, "Total debits must equal total credits"):
            acc_cruds.journal_entry.create_with_items(self.db, obj_in=entry_in)

    def test_create_journal_entry_item_both_debit_credit_raises_error(self):
        data = self.setup_basic_accounting_data()
        items_in = [
            acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("100.00"), credit_amount=Decimal("50.00")),
            acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("50.00")),
        ]
        entry_in = acc_models.JournalEntryCreate(
            entry_date=date(2023,3,17), description="Test item both debit/credit", fiscal_year_id=data["fy"].id, items=items_in
        )
        with self.assertRaisesRegex(ValueError, "An item cannot have both debit and credit amounts"):
            acc_cruds.journal_entry.create_with_items(self.db, obj_in=entry_in)

    def test_get_journal_items_for_account(self):
        data = self.setup_basic_accounting_data()
        acc_cruds.journal_entry.create_with_items(self.db, obj_in=acc_models.JournalEntryCreate(
            entry_date=date(2023, 4, 1), description="Cash Sale 1", fiscal_year_id=data["fy"].id,
            items=[
                acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("200.00")),
                acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("200.00"))
            ]
        ))
        acc_cruds.journal_entry.create_with_items(self.db, obj_in=acc_models.JournalEntryCreate(
            entry_date=date(2023, 4, 5), description="Office Expense Payment", fiscal_year_id=data["fy"].id,
            items=[
                acc_models.JournalItemCreate(account_id=data["expense"].id, debit_amount=Decimal("50.00")),
                acc_models.JournalItemCreate(account_id=data["cash"].id, credit_amount=Decimal("50.00"))
            ]
        ))

        cash_items = acc_cruds.journal_item.get_items_for_account(self.db, account_id=data["cash"].id)
        self.assertEqual(len(cash_items), 2)

        cash_debits = sum(item.debit_amount for item in cash_items)
        cash_credits = sum(item.credit_amount for item in cash_items)
        self.assertEqual(cash_debits, Decimal("200.00"))
        self.assertEqual(cash_credits, Decimal("50.00"))

    def test_create_financial_statement(self):
        data = self.setup_basic_accounting_data()
        stmt_data = {"balance_sheet_items": [{"account": "Cash", "balance": "1000.00"}]}
        stmt_in = acc_models.FinancialStatementCreate(
            name="Balance Sheet Q1 2023",
            statement_type=acc_models.FinancialStatementTypeEnum.BALANCE_SHEET,
            fiscal_year_id=data["fy"].id,
            period_start_date=date(2023, 1, 1),
            period_end_date=date(2023, 3, 31),
            data_json=stmt_data
        )
        stmt = acc_cruds.financial_statement.create(self.db, obj_in=stmt_in)
        self.assertIsNotNone(stmt)
        self.assertEqual(stmt.name, "Balance Sheet Q1 2023")
        self.assertEqual(stmt.data_json, stmt_data)

    def test_get_trial_balance(self):
        data = self.setup_basic_accounting_data()

        acc_cruds.journal_entry.create_with_items(self.db, obj_in=acc_models.JournalEntryCreate(
            entry_date=date(2023, 1, 10), description="Sale 1", fiscal_year_id=data["fy"].id,
            items=[
                acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("500.00")),
                acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("500.00"))
            ]
        ))
        acc_cruds.journal_entry.create_with_items(self.db, obj_in=acc_models.JournalEntryCreate(
            entry_date=date(2023, 1, 15), description="Expense 1", fiscal_year_id=data["fy"].id,
            items=[
                acc_models.JournalItemCreate(account_id=data["expense"].id, debit_amount=Decimal("75.00")),
                acc_models.JournalItemCreate(account_id=data["cash"].id, credit_amount=Decimal("75.00"))
            ]
        ))
        acc_cruds.journal_entry.create_with_items(self.db, obj_in=acc_models.JournalEntryCreate(
            entry_date=date(2023, 1, 20), description="Sale 2", fiscal_year_id=data["fy"].id,
            items=[
                acc_models.JournalItemCreate(account_id=data["cash"].id, debit_amount=Decimal("300.00")),
                acc_models.JournalItemCreate(account_id=data["revenue"].id, credit_amount=Decimal("300.00"))
            ]
        ))

        trial_balance = acc_cruds.get_trial_balance(self.db, fiscal_year_id=data["fy"].id, until_date=date(2023, 1, 31))

        self.assertEqual(len(trial_balance), 3)

        total_debits_report = sum(item['total_debit'] for item in trial_balance)
        total_credits_report = sum(item['total_credit'] for item in trial_balance)

        self.assertEqual(total_debits_report, Decimal("875.00"))
        self.assertEqual(total_credits_report, Decimal("875.00"))

        cash_row = next(item for item in trial_balance if item['account_code'] == data["cash"].code)
        revenue_row = next(item for item in trial_balance if item['account_code'] == data["revenue"].code)
        expense_row = next(item for item in trial_balance if item['account_code'] == data["expense"].code)

        self.assertEqual(cash_row['total_debit'], Decimal("800.00"))
        self.assertEqual(cash_row['total_credit'], Decimal("75.00"))
        self.assertEqual(cash_row['balance'], Decimal("725.00"))

        self.assertEqual(revenue_row['total_debit'], Decimal("0.00"))
        self.assertEqual(revenue_row['total_credit'], Decimal("800.00"))
        self.assertEqual(revenue_row['balance'], Decimal("800.00"))

        self.assertEqual(expense_row['total_debit'], Decimal("75.00"))
        self.assertEqual(expense_row['total_credit'], Decimal("0.00"))
        self.assertEqual(expense_row['balance'], Decimal("75.00"))
