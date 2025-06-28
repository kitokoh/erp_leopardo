# Invoice OCR Expense Tracker

This project provides a command-line tool to extract relevant information from invoice images using Optical Character Recognition (OCR) technology. The extracted data is then persisted into an SQLite database, allowing users to track expenses, manage payment statuses, and generate simple financial summaries.

The primary goal is to simplify expense tracking by automating data entry from invoices.

## Features

*   **OCR Processing:** Extracts text from invoice images (PNG, JPG, etc.) using Tesseract OCR.
*   **Data Parsing:** Parses the extracted text to identify key invoice fields:
    *   Supplier Name
    *   Invoice Number
    *   Invoice Date
    *   Total Amount
    *   Currency (basic inference)
*   **Database Storage:** Stores extracted invoice data in an SQLite database.
*   **CLI Interface:** Provides command-line operations to:
    *   Initialize the database.
    *   Process new invoice images.
    *   List stored invoices with optional status filtering.
    *   Update the payment status of invoices (e.g., from 'À payer' to 'Payée').
    *   Generate a summary expense report.
*   **Payment Status Management:** Tracks whether invoices are 'À payer' (To Pay) or 'Payée' (Paid).
*   **Basic Reporting:** Offers a simple expense summary (total invoices, paid/unpaid amounts, spending by supplier).

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.8 or higher is recommended.
2.  **Tesseract OCR Engine:** This is crucial for the OCR functionality.
    *   **Linux (Debian/Ubuntu):**
        ```bash
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
        # (Installs English and French language packs; add others if needed)
        ```
    *   **macOS:**
        ```bash
        brew install tesseract tesseract-lang
        # (tesseract-lang installs all available language packs)
        # To install specific languages: brew install tesseract tesseract-lang-<langcode>
        ```
    *   **Windows:**
        1.  Download the Tesseract installer from the [Tesseract at UB Mannheim GitHub page](https://github.com/UB-Mannheim/tesseract/wiki).
        2.  Run the installer. **Important:** During installation, make sure to:
            *   Select additional language data (e.g., French, English) if not included by default.
            *   Ensure that Tesseract is added to your system's PATH environment variable. You might need to do this manually if the installer doesn't provide an option or if it's not effective (e.g., add `C:\Program Files\Tesseract-OCR` to PATH).

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url> # Replace <your-repository-url> with the actual URL
    cd invoice-ocr-project
    # Note: The project directory in the repository is 'invoice_ocr_project'.
    # If you clone the root, cd into 'invoice_ocr_project'.
    # For simplicity, this README assumes you are in the 'invoice_ocr_project' directory.
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```

3.  **Install Python Dependencies:**
    Ensure your virtual environment is activated.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database:**
    This command creates the `invoice_database.db` file (if it doesn't exist) and sets up the necessary tables.
    ```bash
    python src/main.py initdb
    ```
    You should see a confirmation message.

## CLI Usage

All commands are run from the `invoice_ocr_project` directory using `python src/main.py <command> [options]`.

### 1. Initialize Database
Ensures the database and its tables are correctly set up. Safe to run multiple times.
```bash
python src/main.py initdb
```

### 2. Process an Invoice Image
Extracts data from an invoice image and saves it to the database.
```bash
python src/main.py process /path/to/your/invoice.png
```
Replace `/path/to/your/invoice.png` with the actual path to your invoice image file (e.g., JPG, PNG, TIFF).

**Example:**
```bash
# Assuming dummy_invoice_test.png is in the current directory (it's created by ocr_processor.py for testing)
python src/main.py process dummy_invoice_test.png
```

### 3. List Invoices
Displays invoices stored in the database.
```bash
python src/main.py list
```
**Optional Filtering by Status:**
```bash
python src/main.py list --status "À payer"
python src/main.py list --status "Payée"
```

### 4. Update Invoice Status
Changes the payment status of an invoice and can optionally set the payment date.
```bash
python src/main.py update <INVOICE_ID> <NEW_STATUS> [--payment_date YYYY-MM-DD]
```
*   `<INVOICE_ID>`: The ID of the invoice (from the `list` command).
*   `<NEW_STATUS>`: The new status, either `'À payer'` or `'Payée'` (must be quoted if it contains spaces).
*   `--payment_date YYYY-MM-DD` (Optional): Sets the payment date. If `NEW_STATUS` is `'Payée'` and this is omitted, the current date is used.

**Examples:**
```bash
python src/main.py update 1 "Payée"
python src/main.py update 2 "Payée" --payment_date 2023-11-20
python src/main.py update 3 "À payer"
```

### 5. Generate Expense Report
Displays a summary of expense data.
```bash
python src/main.py report
```
The report includes:
*   Total number of invoices.
*   Count and total amount for paid invoices.
*   Count and total amount for unpaid invoices.
*   Total spending grouped by supplier.
*   **Note:** Monetary totals currently sum amounts directly and do not convert between different currencies.

## Running Tests

To run the unit tests, navigate to the `invoice_ocr_project` directory (if not already there) and run:
```bash
python -m unittest discover tests
```
This will discover and execute all tests in the `tests` directory.

## Project Structure

invoice_ocr_project/
|-- src/                    # Source code
|   |-- __init__.py
|   |-- ocr_processor.py    # Handles OCR logic and text parsing.
|   |-- database_manager.py # Handles SQLite database interactions.
|   |-- main.py             # CLI entry point and command handlers.
|   |-- utils.py            # Utility functions (currently a placeholder).
|-- tests/                  # Unit tests
|   |-- __init__.py
|   |-- test_ocr_processor.py
|   |-- test_database_manager.py
|-- invoices_data/          # (Optional) Suggested directory for storing invoice images
|   |-- raw_images/
|-- requirements.txt        # Python dependencies.
|-- invoice_database.db     # SQLite database file (created by `initdb` or first run).
|-- dummy_invoice_test.png  # A sample image created by ocr_processor.py for testing.
`-- README.md               # This file.

## OCR Parsing Details & Limitations

*   **Method:** The current implementation uses regular expressions (regex) and rule-based string matching to parse information from the raw text extracted by Tesseract OCR.
*   **Key Fields Extracted:**
    *   Supplier Name (naive: first non-empty line from top)
    *   Invoice Number
    *   Invoice Date (attempts multiple common formats like DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD)
    *   Total Amount
    *   Currency (basic inference from symbols like $, €, £ or codes like USD, EUR, XOF found on the same line as the total amount)
*   **Limitations:**
    *   **Layout Sensitivity:** Performance is highly dependent on the clarity and layout of the invoice. Complex layouts, handwritten text, or poor image quality can significantly degrade accuracy.
    *   **Supplier Name Extraction:** The current method is very basic and may not always be accurate.
    *   **Date Disambiguation:** If multiple dates are present, it currently picks the first valid one found. Distinguishing between invoice date, due date, etc., is rudimentary. Due date extraction is not yet implemented.
    *   **Tax and Line Items:** Tax amount and detailed line item extraction are not currently implemented.
    *   **Specific Formats:** While efforts were made to handle common formats, some specific invoice structures might not be parsed correctly. For instance, the amount for "Net à payer XOF 50000" is a known parsing limitation (currency is identified, but amount is not reliably extracted by the total amount regex for this specific keyword-currency-amount sequence).
    *   **Currency Aggregation:** The expense report sums total amounts directly without converting between currencies. This means aggregated totals might be misleading if invoices use different currencies.

## Potential Future Enhancements

*   **Graphical User Interface (GUI):** A web-based or desktop GUI for easier interaction.
*   **Improved OCR & Preprocessing:**
    *   Implement advanced image preprocessing steps (e.g., deskewing, noise reduction, binarization) in `ocr_processor.py`.
    *   Explore alternative OCR engines or cloud-based OCR services (e.g., Google Cloud Vision AI, AWS Textract) for potentially higher accuracy, especially for complex documents.
*   **Advanced Parsing:**
    *   Utilize Natural Language Processing (NLP) techniques or Machine Learning models for more robust and context-aware information extraction.
    *   Integrate dedicated parsing libraries.
*   **Broader Format Support:** Enhance regex and parsing logic to support a wider variety of invoice layouts and languages.
*   **Detailed Data Extraction:** Implement extraction for line items, tax details, due dates, etc.
*   **Configuration:** Use a configuration file for settings like database path, Tesseract options, etc.
*   **Multi-Currency Handling:** Implement proper currency conversion or grouped summaries by currency in reports.
