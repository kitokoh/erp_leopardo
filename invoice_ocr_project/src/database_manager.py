import sqlite3
from datetime import datetime

DATABASE_NAME = "invoice_database.db"
"""
The name of the SQLite database file.
It will be created in the current working directory from where the application is run
(e.g., in `invoice_ocr_project/` if running `python src/main.py` from there).
"""

# This module-level variable was an earlier idea for tests, but explicit connection passing is preferred.
# _active_test_connection = None

def get_db_connection(conn_override: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """
    Establishes and returns a connection to the SQLite database.

    The connection is configured to use `sqlite3.Row` as its `row_factory`,
    allowing dictionary-like access (by column name) to query results.

    Args:
        conn_override: If a `sqlite3.Connection` object is provided,
                       this function will return it directly. This is primarily
                       used for testing to allow operations on a specific
                       test database connection (e.g., an in-memory database).

    Returns:
        A `sqlite3.Connection` object to the database.
    """
    if conn_override:
        return conn_override

    # If DATABASE_NAME is ":memory:", each call to sqlite3.connect(":memory:")
    # typically creates a new, independent in-memory database.
    # For testing, it's crucial that all operations in a single test method
    # use the exact same connection object if an in-memory database is intended
    # to persist across function calls within that test. This is handled by
    # passing conn_override from the test's self.conn.

    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn: sqlite3.Connection | None = None) -> None:
    """
    Creates the `invoices` table in the database if it doesn't already exist.

    The table schema is defined to store extracted invoice information,
    including filenames, supplier details, amounts, dates, payment status,
    and the raw OCR text. It includes UNIQUE constraints to prevent duplicate
    entries based on invoice number and a combination of filename and invoice number.

    Args:
        conn: An optional `sqlite3.Connection` object. If provided, tables
              will be created using this connection. Otherwise, a new
              connection is established.
    """
    close_conn_locally = False
    if conn is None:
        conn = get_db_connection()
        close_conn_locally = True

    cursor = conn.cursor()

    # Schema definition for the 'invoices' table
    # - invoice_number: Marked UNIQUE assuming it should be globally unique. If not, this constraint should be removed.
    # - unique_invoice_file: A composite UNIQUE constraint on (filename, invoice_number) to prevent
    #   re-processing and storing the exact same invoice file if it yields the same invoice number.
    # - Dates (invoice_date, due_date, payment_date): Stored as TEXT in 'YYYY-MM-DD' format.
    # - upload_timestamp: Stored as TEXT in ISO 8601 format.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        supplier_name TEXT,
        invoice_number TEXT UNIQUE, -- Assuming invoice numbers should be unique
        invoice_date TEXT,          -- Store as TEXT in YYYY-MM-DD format
        due_date TEXT,              -- Store as TEXT in YYYY-MM-DD format
        total_amount REAL,          -- REAL for floating point numbers
        currency TEXT,
        tax_amount REAL,
        items_description TEXT,
        payment_status TEXT NOT NULL DEFAULT 'À payer', -- Default status
        payment_date TEXT,          -- Store as TEXT in YYYY-MM-DD format
        upload_timestamp TEXT NOT NULL, -- Store as TEXT in ISO format
        extracted_text TEXT,
        CONSTRAINT unique_invoice_file UNIQUE (filename, invoice_number) -- Optional: ensure combination is unique
    );
    """)
    # Note: SQLite DATE type is actually TEXT, so storing as YYYY-MM-DD is good practice.
    # For TIMESTAMP, TEXT in ISO 8601 format (YYYY-MM-DD HH:MM:SS.SSS) is standard.
    # UNIQUE constraint on invoice_number might be too strict if multiple suppliers use same number format.
    # A composite UNIQUE constraint on (supplier_name, invoice_number) might be better if needed.
    # For now, `invoice_number TEXT UNIQUE` is a simple start. If it causes issues, we can remove it.
    # Added `UNIQUE (filename, invoice_number)` as a more robust way to prevent duplicate entries of the same processed invoice.

    conn.commit()
    if close_conn_locally:
        conn.close()
    # print("Database tables checked/created successfully.") # Quieter for tests

def save_invoice_data(invoice_data: dict, original_filename: str = "", conn: sqlite3.Connection | None = None) -> int | None:
    """
    Saves extracted invoice data to the `invoices` table in the database.

    Args:
        invoice_data: A dictionary containing the parsed invoice information.
                      Expected keys correspond to the columns in the `invoices` table
                      (e.g., 'supplier_name', 'invoice_number', 'total_amount').
        original_filename: The filename of the processed invoice image.
        conn: An optional `sqlite3.Connection` object. If provided, this
              connection is used for the database operation. Otherwise, a new
              connection is established.

    Returns:
        The ID of the newly inserted row if successful, None otherwise.
        Prints an error message if saving fails (e.g., due to a UNIQUE
        constraint violation or other database error).
    """
    if not invoice_data:
        print("Warning: No invoice data provided to save.")
        return None

    close_conn_locally = False
    if conn is None:
        conn = get_db_connection()
        close_conn_locally = True

    cursor = conn.cursor()

    # Prepare data for insertion, using .get() for optional fields
    # and ensuring correct types or defaults.
    upload_ts = datetime.now().isoformat()

    # Default status is 'À payer', handled by table schema if not provided
    payment_status = invoice_data.get('payment_status', 'À payer')

    try:
        cursor.execute("""
        INSERT INTO invoices (
            filename, supplier_name, invoice_number, invoice_date, due_date,
            total_amount, currency, tax_amount, items_description,
            payment_status, payment_date, upload_timestamp, extracted_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            original_filename,
            invoice_data.get('supplier_name'),
            invoice_data.get('invoice_number'),
            invoice_data.get('invoice_date'), # Assumed YYYY-MM-DD from parser
            invoice_data.get('due_date'),     # Assumed YYYY-MM-DD
            invoice_data.get('total_amount'), # Should be float
            invoice_data.get('currency'),
            invoice_data.get('tax_amount'),   # Should be float
            invoice_data.get('items_description'),
            payment_status,
            invoice_data.get('payment_date'), # Assumed YYYY-MM-DD
            upload_ts,
            invoice_data.get('raw_text')      # Full text from OCR
        ))
        conn.commit()
        inserted_id = cursor.lastrowid
        print(f"Invoice data for '{original_filename}' (Inv #: {invoice_data.get('invoice_number')}) saved successfully with ID: {inserted_id}.")
        return inserted_id
    except sqlite3.IntegrityError as e:
        # This can happen if UNIQUE constraint is violated (e.g., same invoice_number)
        print(f"Error saving invoice data for '{original_filename}': {e}")
        print("This might be due to a duplicate invoice number or filename combination.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while saving invoice data for '{original_filename}': {e}")
        conn.rollback() # Rollback in case of other errors
        return None
    finally:
        if close_conn_locally:
            conn.close()

def get_invoice_by_id(invoice_id: int, conn: sqlite3.Connection | None = None) -> sqlite3.Row | None:
    """
    Retrieves a single invoice record from the database by its primary key (ID).

    Args:
        invoice_id: The ID of the invoice to retrieve.
        conn: An optional `sqlite3.Connection` object.

    Returns:
        A `sqlite3.Row` object representing the invoice if found (allows
        dictionary-like access by column name), otherwise None.
    """
    close_conn_locally = False
    if conn is None:
        conn = get_db_connection()
        close_conn_locally = True

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    invoice = cursor.fetchone()

    if close_conn_locally:
        conn.close()
    return invoice

def get_all_invoices(status_filter: str | None = None, conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    """
    Retrieves all invoice records from the database, ordered by upload timestamp
    in descending order (newest first). Optionally filters by payment status.

    Args:
        status_filter: An optional string to filter invoices by their
                       `payment_status` (e.g., 'À payer', 'Payée').
        conn: An optional `sqlite3.Connection` object.

    Returns:
        A list of `sqlite3.Row` objects, each representing an invoice.
        Returns an empty list if no invoices match the criteria.
    """
    close_conn_locally = False
    if conn is None:
        conn = get_db_connection()
        close_conn_locally = True

    cursor = conn.cursor()
    query = "SELECT * FROM invoices"
    params = []
    if status_filter:
        query += " WHERE payment_status = ?"
        params.append(status_filter)
    query += " ORDER BY upload_timestamp DESC" # Show newest first

    cursor.execute(query, params)
    invoices = cursor.fetchall()

    if close_conn_locally:
        conn.close()
    return invoices # Returns a list of Row objects

def update_invoice_status(invoice_id: int, new_status: str,
                          payment_date_str: str | None = None,
                          conn: sqlite3.Connection | None = None) -> bool:
    """
    Updates the payment status and optionally the payment date of a specific invoice.

    If `new_status` is 'Payée' and `payment_date_str` is not provided,
    the payment date defaults to the current date.

    Args:
        invoice_id: The ID of the invoice to update.
        new_status: The new payment status (e.g., 'Payée', 'À payer').
        payment_date_str: An optional payment date string in 'YYYY-MM-DD' format.
                          If None and status is 'Payée', current date is used.
                          Set to None if status is not 'Payée' and no specific
                          date needs to be cleared/set.
        conn: An optional `sqlite3.Connection` object.

    Returns:
        True if the update was successful (at least one row affected),
        False otherwise (e.g., invoice ID not found, or database error).
    """
    close_conn_locally = False
    if conn is None:
        conn = get_db_connection()
        close_conn_locally = True

    cursor = conn.cursor()
    try:
        if new_status == "Payée" and payment_date_str is None:
            # If marking as paid, and no payment date is given, use today's date.
            payment_date_str = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
        UPDATE invoices
        SET payment_status = ?, payment_date = ?
        WHERE id = ?
        """, (new_status, payment_date_str, invoice_id))

        conn.commit()
        if cursor.rowcount > 0:
            print(f"Invoice ID {invoice_id} status updated to '{new_status}'.")
            return True
        else:
            print(f"Invoice ID {invoice_id} not found for status update.")
            return False
    except Exception as e:
        print(f"Error updating invoice status for ID {invoice_id}: {e}")
        conn.rollback()
        return False
    finally:
        if close_conn_locally:
            conn.close()

def get_expense_summary(conn: sqlite3.Connection | None = None) -> dict:
    """
    Calculates and returns a summary of invoice data from the database.

    The summary includes:
    - Total number of invoices.
    - Count of paid invoices and their total amount.
    - Count of unpaid invoices ('À payer') and their total amount.
    - A dictionary of total spending per supplier.

    Note:
        Monetary sums currently do not differentiate between currencies.
        If invoices use multiple currencies, these sums will be direct additions
        of the amounts, which might not be meaningful without conversion.

    Args:
        conn: An optional `sqlite3.Connection` object.

    Returns:
        A dictionary containing the expense summary. Keys include:
        'total_invoices', 'paid_invoices_count', 'total_paid_amount',
        'unpaid_invoices_count', 'total_unpaid_amount', 'spending_by_supplier'.
        Amounts are floats, counts are integers. 'spending_by_supplier'
        is a dict of {supplier_name: total_amount}.
    """
    close_conn_locally = False
    if conn is None:
        conn = get_db_connection()
        close_conn_locally = True

    cursor = conn.cursor()

    summary = {
        "total_invoices": 0,
        "paid_invoices_count": 0,
        "unpaid_invoices_count": 0,
        "total_paid_amount": 0.0,
        "total_unpaid_amount": 0.0,
        "spending_by_supplier": {} # {supplier_name: total_amount}
    }

    try:
        # Total invoices
        cursor.execute("SELECT COUNT(*) FROM invoices")
        summary["total_invoices"] = cursor.fetchone()[0]

        # Paid invoices count and total amount
        cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM invoices WHERE payment_status = 'Payée'")
        paid_data = cursor.fetchone()
        summary["paid_invoices_count"] = paid_data[0] if paid_data[0] is not None else 0
        summary["total_paid_amount"] = paid_data[1] if paid_data[1] is not None else 0.0

        # Unpaid invoices count and total amount
        cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM invoices WHERE payment_status = 'À payer'")
        unpaid_data = cursor.fetchone()
        summary["unpaid_invoices_count"] = unpaid_data[0] if unpaid_data[0] is not None else 0
        summary["total_unpaid_amount"] = unpaid_data[1] if unpaid_data[1] is not None else 0.0

        # Spending by supplier (considering all invoices, could be filtered by status if needed)
        # For simplicity, sums all amounts regardless of currency. Proper handling would group by currency.
        cursor.execute("""
            SELECT supplier_name, SUM(total_amount) as total_spent
            FROM invoices
            WHERE supplier_name IS NOT NULL AND total_amount IS NOT NULL
            GROUP BY supplier_name
            ORDER BY total_spent DESC
        """)
        supplier_spending = cursor.fetchall()
        for row in supplier_spending:
            summary["spending_by_supplier"][row['supplier_name']] = row['total_spent']

    except Exception as e:
        print(f"Error calculating expense summary: {e}")
        # Return partially filled summary or None/empty if critical error
    finally:
        if close_conn_locally:
            conn.close()

    return summary

# --- Example Usage & Initialization ---
if __name__ == '__main__':
    # This main block will use the default behavior (creating its own connections)
    print(f"Database will be created/used: {DATABASE_NAME}")
    db_conn_main = get_db_connection() # Get a connection for the main block
    create_tables(conn=db_conn_main) # Ensure tables exist using this connection

    # Example: Simulating data from ocr_processor
    sample_ocr_data = {
        'supplier_name': 'Fournisseur Test SA',
        'invoice_number': 'FT2023-001',
        'invoice_date': '2023-10-01',
        'due_date': '2023-10-31',
        'total_amount': 150.75,
        'currency': 'EUR',
        'tax_amount': 25.12,
        'items_description': 'Service de test, Produit de démonstration',
        'raw_text': 'Blah blah blah facture text FT2023-001 ... Total 150.75 EUR ...',
        # payment_status will default to 'À payer'
    }

    dummy_filename = "test_invoice_001.pdf"

    # Test saving
    inserted_id = save_invoice_data(sample_ocr_data, dummy_filename)

    if inserted_id:
        print(f"\n--- Fetching invoice ID: {inserted_id} ---")
        invoice = get_invoice_by_id(inserted_id)
        if invoice:
            for key in invoice.keys():
                print(f"{key}: {invoice[key]}")

        print(f"\n--- Updating status for invoice ID: {inserted_id} to 'Payée' ---")
        update_invoice_status(inserted_id, "Payée")

        invoice_updated = get_invoice_by_id(inserted_id)
        if invoice_updated:
            print(f"New status: {invoice_updated['payment_status']}, Payment date: {invoice_updated['payment_date']}")

    print("\n--- Fetching all invoices ---")
    all_invoices = get_all_invoices()
    if all_invoices:
        for inv in all_invoices:
            print(f"ID: {inv['id']}, Inv#: {inv['invoice_number']}, Supplier: {inv['supplier_name']}, Status: {inv['payment_status']}, Total: {inv['total_amount']} {inv['currency']}")
    else:
        print("No invoices found.")

    # Example of trying to insert a duplicate (should fail if invoice_number is UNIQUE or filename+inv_num is UNIQUE)
    print("\n--- Attempting to save duplicate invoice data (should trigger IntegrityError) ---")
    # Modify slightly to avoid exact same timestamp for different test if not for unique constraint
    sample_ocr_data_dup = sample_ocr_data.copy()
    # sample_ocr_data_dup['supplier_name'] = 'Another Supplier With Same Inv No' # to test only inv_no unique

    save_invoice_data(sample_ocr_data_dup, dummy_filename) # Same filename and inv_number

    print("\n--- Fetching 'À payer' invoices ---")
    unpaid_invoices = get_all_invoices(status_filter='À payer')
    if unpaid_invoices:
        for inv in unpaid_invoices:
             print(f"ID: {inv['id']}, Inv#: {inv['invoice_number']}, Status: {inv['payment_status']}")
    else:
        print("No 'À payer' invoices found.")
    # The second (older) get_expense_summary and if __name__ == '__main__' block will be removed by this empty replace.
