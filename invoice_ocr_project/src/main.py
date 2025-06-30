import argparse
import os
# from . import ocr_processor # Use explicit relative import
# from . import database_manager # Use explicit relative import

# Path adjustment for direct script execution vs. module execution
import sys
from pathlib import Path

# --- Module Import Handling ---
# This block allows the script to be run directly (e.g., `python src/main.py`)
# or as part of a package (e.g., `python -m invoice_ocr_project.src.main`).
if __package__ is None or __package__ == '':
    # Executed as a script: Add the 'src' directory to sys.path
    # to allow direct imports of sibling modules.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ocr_processor
    import database_manager
else:
    # Executed as a module: Use relative imports.
    from . import ocr_processor
    from . import database_manager

# --- CLI Command Handlers ---

def handle_process_invoice(args: argparse.Namespace) -> None:
    """
    Handles the 'process' command from the CLI.

    This function takes an image path from the command-line arguments,
    processes the invoice image to extract data using the ocr_processor module,
    and then saves the extracted data to the database via the database_manager module.
    It ensures the database tables are created before processing.

    Args:
        args: An argparse.Namespace object containing the parsed command-line
              arguments. Expected to have an 'image_path' attribute.
    """
    image_path = args.image_path
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at '{image_path}'")
        return

    print(f"Processing invoice image: {image_path}...")
    # Ensure database is initialized before processing
    database_manager.create_tables() # Idempotent: creates if not exists

    extracted_data = ocr_processor.process_invoice_image(image_path)
    if extracted_data:
        filename = os.path.basename(image_path)
        db_id = database_manager.save_invoice_data(extracted_data, original_filename=filename)
        if db_id:
            print(f"Invoice processed and saved with ID: {db_id}")
        else:
            print("Failed to save invoice data to the database.")
    else:
        print("Failed to extract data from invoice image.")

def handle_list_invoices(args: argparse.Namespace) -> None:
    """
    Handles the 'list' command from the CLI.

    Retrieves and displays all invoices from the database, optionally
    filtering by payment status. Ensures database tables are created.
    Output is formatted as a simple table.

    Args:
        args: An argparse.Namespace object. Expected to have an optional
              'status' attribute for filtering.
    """
    print("Listing invoices...")
    if args.status:
        print(f"Filter by status: {args.status}")

    database_manager.create_tables() # Ensure DB is initialized

    invoices = database_manager.get_all_invoices(status_filter=args.status)
    if not invoices:
        print("No invoices found." + (f" with status '{args.status}'." if args.status else "."))
        return

    print(f"\nFound {len(invoices)} invoice(s):")
    print("-" * 80)
    print(f"{'ID':<5} | {'Filename':<25} | {'Supplier':<20} | {'Inv #':<15} | {'Date':<10} | {'Total':<10} | {'Status':<10}")
    print("-" * 80)
    for inv in invoices:
        total_str = f"{inv['total_amount'] or ''} {inv['currency'] or ''}".strip()
        print(f"{inv['id']:<5} | {inv['filename'][:25]:<25} | {str(inv['supplier_name'] or '')[:20]:<20} | {str(inv['invoice_number'] or '')[:15]:<15} | {str(inv['invoice_date'] or '')[:10]:<10} | {total_str[:10]:<10} | {str(inv['payment_status'] or '')[:10]:<10}")
    print("-" * 80)


def handle_update_status(args: argparse.Namespace) -> None:
    """
    Handles the 'update' command from the CLI.

    Updates the payment status and optionally the payment date of a specified invoice.
    Ensures database tables are created and validates payment date format if provided.

    Args:
        args: An argparse.Namespace object containing 'invoice_id', 'new_status',
              and an optional 'payment_date'.
    """
    invoice_id = args.invoice_id
    new_status = args.new_status
    payment_date = args.payment_date # This is a string or None

    if payment_date:
        try:
            from datetime import datetime # Local import for type checking
            datetime.strptime(payment_date, '%Y-%m-%d')
        except ValueError:
            print("Error: Payment date must be in YYYY-MM-DD format (e.g., 2023-12-31).")
            return

    database_manager.create_tables() # Ensure DB is initialized

    print(f"Updating status for invoice ID {invoice_id} to '{new_status}'" +
          (f" with payment date {payment_date}" if payment_date else ""))

    success = database_manager.update_invoice_status(invoice_id, new_status, payment_date_str=payment_date)
    if success:
        print("Invoice status updated successfully.")
    else:
        print("Failed to update invoice status. Please check if the invoice ID is correct.")

def handle_init_db(args: argparse.Namespace) -> None:
    """
    Handles the 'initdb' command from the CLI.

    Initializes the database by ensuring that the necessary tables (e.g., 'invoices')
    are created according to the schema defined in `database_manager.py`.

    Args:
        args: An argparse.Namespace object (not used in this function but
              part of the subparser interface).
    """
    print("Initializing database...")
    database_manager.create_tables()
    print("Database initialization complete. Tables schema checked/created.")

def handle_report(args: argparse.Namespace) -> None:
    """
    Handles the 'report' command from the CLI.

    Generates and displays an expense summary report based on the data
    stored in the invoices database. Ensures database tables are created.

    Args:
        args: An argparse.Namespace object (not used in this function).
    """
    print("\nGenerating Expense Report...")
    database_manager.create_tables() # Ensure DB is initialized

    summary = database_manager.get_expense_summary()

    if not summary or summary.get('total_invoices', 0) == 0:
        print("No invoice data available to generate a report.")
        return

    print("\n--- Expense Summary ---")
    print(f"Total Invoices: {summary['total_invoices']}")
    print(f"Paid Invoices: {summary['paid_invoices_count']} (Total Amount: {summary['total_paid_amount']:.2f})") # Assumes consistent currency
    print(f"Unpaid Invoices ('À payer'): {summary['unpaid_invoices_count']} (Total Amount: {summary['total_unpaid_amount']:.2f})") # Assumes consistent currency

    if summary['spending_by_supplier']:
        print("\n--- Spending by Supplier ---")
        # Sort suppliers by amount for better readability
        sorted_suppliers = sorted(summary['spending_by_supplier'].items(), key=lambda item: item[1], reverse=True)
        for supplier, total in sorted_suppliers:
            print(f"  - {supplier}: {total:.2f}") # Assumes consistent currency
    else:
        print("\nNo supplier-specific spending data available.")
    print("-----------------------\n")
    print("Note: Monetary totals sum amounts directly; they do not currently convert between different currencies.")

# --- Main CLI Setup and Execution ---

def main() -> None:
    """
    Sets up and runs the command-line interface for invoice processing.

    This function initializes argparse to define and handle various sub-commands
    for interacting with the invoice OCR and database functionalities, such as
    initializing the database, processing new invoices, listing existing ones,
    updating their status, and generating reports.
    """
    parser = argparse.ArgumentParser(
        description="Invoice OCR Management CLI - A tool to extract data from invoice images and manage expenses.",
        epilog="Example: python src/main.py process /path/to/invoice.png"
    )
    subparsers = parser.add_subparsers(
        title="Available Commands",
        dest="command",
        required=True,
        help="Use '<command> --help' for more information on a specific command."
    )

    # 'initdb' command: Initializes the database.
    parser_initdb = subparsers.add_parser(
        "initdb",
        help="Initialize the database (create tables if they don't exist).",
        description="Ensures the database schema is set up correctly. Safe to run multiple times."
    )
    parser_initdb.set_defaults(func=handle_init_db)

    # 'process' command: Processes a single invoice image.
    parser_process = subparsers.add_parser(
        "process",
        help="Process an invoice image, extract data, and save to database.",
        description="Takes an image file path, performs OCR, parses relevant fields, and stores them."
    )
    parser_process.add_argument(
        "image_path",
        metavar="IMAGE_PATH",
        help="Path to the invoice image file (e.g., invoice.png, scan.jpg)."
    )
    parser_process.set_defaults(func=handle_process_invoice)

    # 'list' command: Lists invoices from the database.
    parser_list = subparsers.add_parser(
        "list",
        help="List invoices from the database, with optional status filter.",
        description="Displays stored invoices. Can be filtered by payment status ('À payer', 'Payée')."
    )
    parser_list.add_argument(
        "--status",
        help="Filter invoices by payment status (e.g., 'À payer', 'Payée').",
        choices=['À payer', 'Payée'], # Restrict choices for status
        default=None # Ensure it's None if not provided, not an empty string
    )
    parser_list.set_defaults(func=handle_list_invoices)

    # 'update' command: Updates the status of an invoice.
    parser_update = subparsers.add_parser(
        "update",
        help="Update the payment status and optionally payment date of an invoice.",
        description="Marks an invoice with a new status (e.g., 'Payée'). Payment date can also be set."
    )
    parser_update.add_argument(
        "invoice_id",
        type=int,
        metavar="INVOICE_ID",
        help="ID of the invoice to update (as shown in 'list' command)."
    )
    parser_update.add_argument(
        "new_status",
        metavar="NEW_STATUS",
        help="New payment status (e.g., 'Payée', 'À payer').",
        choices=['À payer', 'Payée'] # Restrict choices
    )
    parser_update.add_argument(
        "--payment_date",
        help="Optional payment date in YYYY-MM-DD format (e.g., 2023-12-31). Recommended if status is 'Payée'."
    )
    parser_update.set_defaults(func=handle_update_status)

    # 'report' command: Generates an expense summary report.
    parser_report = subparsers.add_parser(
        "report",
        help="Generate and display an expense summary report.",
        description="Provides a summary of total invoices, paid/unpaid amounts, and spending by supplier."
    )
    parser_report.set_defaults(func=handle_report)

    args = parser.parse_args()
    if hasattr(args, 'func'): # Check if a sub-command function was set
        args.func(args)
    else:
        parser.print_help() # Should not happen if 'required=True' for subparsers

if __name__ == "__main__":
    # The sys.path manipulation at the top handles import resolution
    # for both direct script execution and module execution.
    main()
