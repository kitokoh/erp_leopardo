import pytesseract
from PIL import Image
import re
from datetime import datetime

# --- Constants for OCR and Parsing ---
# Tesseract Page Segmentation Modes (PSM) can affect OCR results.
# PSM 6: Assume a single uniform block of text. Often good for invoices.
# PSM 3: Fully automatic page segmentation, but no OSD. (Default)
# PSM 11: Sparse text. Find as much text as possible in no particular order.
# PSM 12: Sparse text with OSD.
TESSERACT_CONFIG = r'--oem 3 --psm 6' # OEM 3 is the default Tesseract engine.

# Date formats to attempt parsing with strptime
DATE_FORMATS_TO_TRY = (
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",  # DD/MM/YYYY
    "%Y/%m/%d", "%Y-%m-%d",              # YYYY/MM/DD
    "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",  # MM/DD/YYYY
    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",  # DD/MM/YY (Year with 2 digits)
    "%m/%d/%y", "%m-%d-%y", "%m.%d.%y"   # MM/DD/YY (Year with 2 digits)
)


def preprocess_image(image_path: str) -> Image.Image | None:
    """
    Opens an image file using Pillow.

    This function is a placeholder for more advanced image preprocessing steps
    that could improve OCR accuracy, such as:
    - Grayscale conversion
    - Binarization (thresholding to black and white)
    - Noise reduction
    - Deskewing (correcting tilted images)

    Args:
        image_path: The file path to the image.

    Returns:
        A Pillow Image object if successful, or None if an error occurs
        (e.g., file not found, image format not supported).
    """
    try:
        img = Image.open(image_path)
        # Example of a simple preprocessing step (can be uncommented or expanded):
        # img = img.convert('L')
        return img
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def extract_text_from_image(image_path: str, lang: str = 'fra+eng') -> str | None:
    """
    Extracts text from an image using the Tesseract OCR engine.

    It first preprocesses the image (currently just opening it) and then
    applies Tesseract OCR. The default languages are French and English.

    Args:
        image_path: Path to the image file.
        lang: Language codes for Tesseract (e.g., 'eng', 'fra', 'fra+eng').

    Returns:
        The extracted text as a string if successful, None otherwise.
        Prints error messages if Tesseract is not found or other issues occur.
    """
    try:
        img = preprocess_image(image_path)
        if img is None:
            return None # Error message already printed by preprocess_image

        # TESSERACT_CONFIG is defined as a global constant
        text = pytesseract.image_to_string(img, lang=lang, config=TESSERACT_CONFIG)
        return text
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract is not installed or not in your PATH.")
        print("Please install Tesseract and make sure it's accessible.")
        return None
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return None

def parse_extracted_text(text: str) -> dict:
    """
    Parses raw text (presumably from OCR) to extract structured invoice data.

    This function uses a series of regular expressions and string manipulations
    to identify and extract common invoice fields like supplier name, invoice number,
    dates, and total amount. The parsing logic is rule-based and may require
    adjustments for different invoice layouts or languages.

    Args:
        text: The raw text string to parse.

    Returns:
        A dictionary containing the extracted invoice fields. Fields that
        are not found or parsed successfully will be None or absent.
        Returns an empty dictionary if the input text is empty or None.
    """
    if not text:
        return {}

    extracted_data = {
        "supplier_name": None,
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None, # Placeholder, regex not yet defined
        "total_amount": None,
        "currency": None, # Placeholder, regex not yet defined
        "tax_amount": None, # Placeholder, regex not yet defined
        "items_description": None # Placeholder
    }

    # Regex patterns (these are examples and will need refinement)
    # Date patterns: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY/MM/DD, YYYY-MM-DD
    # More robust date parsing would involve trying multiple formats or using dateparser library
    date_pattern = re.compile(r'(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})')

    # Invoice number patterns (highly variable)
    # Looking for terms like "Facture N°", "Invoice #", followed by alphanumeric string
    invoice_num_pattern = re.compile(r'(?:Facture\s*(?:N[°o.]|No\.?)\s*:?\s*|Invoice\s*(?:No\.?|Number|#)\s*:?\s*)\s*([A-Za-z0-9/\-#]+)', re.IGNORECASE)

    # Total amount patterns (also highly variable)
    # Looks for "Total", "Montant Total", "Total TTC" followed by a number.
    # This needs to be much more robust to handle currency symbols, decimal points, thousands separators.
    total_amount_pattern = re.compile(r'(?:total(?: ttc| ht| à payer| amount)?|montant total|net\s*a\s*payer)\s*:?(?:\s*(?:[\$€£]|[A-Z]{1,5}))?\s*(\d[\d\s.,]*)', re.IGNORECASE)

    # Supplier name: This is the hardest part with regex. Often at the top.
    # For now, let's try to get the first few lines as a potential supplier, or look for common keywords.
    # This will be very unreliable.
    lines = text.split('\n')
    if lines:
        # A very naive way, could be the first non-empty line or a line with "S.A.", "SARL", "Ltd."
        # This is more of a placeholder.
        for i, line in enumerate(lines[:5]): # Check first 5 lines
            if line.strip() and len(line.strip()) > 3: # Basic check for non-empty, reasonable length
                extracted_data["supplier_name"] = line.strip()
                break
                # A better approach might involve looking for address lines, VAT numbers, etc.
                # or matching against a known list of suppliers.

    # Find invoice number
    match_inv_num = invoice_num_pattern.search(text)
    if match_inv_num:
        inv_num_candidate = match_inv_num.group(1).strip()
        # Clean up common prefixes/suffixes if they were captured
        inv_num_candidate = re.sub(r'^(?:facture\s*n(?:[°o:]|\s*du)?|invoice\s*(?:no\.?|number|#)?)\s*', '', inv_num_candidate, flags=re.IGNORECASE)
        extracted_data["invoice_number"] = inv_num_candidate.strip()

    # Find dates
    # We'll take the first valid date found as the invoice date for now.
    # This is a simplification; invoices can have multiple dates (order date, due date).
    found_dates = []
    for line in lines:
        for match in date_pattern.finditer(line):
            date_str = match.group(0)
            # Try to parse the date to standardize format and validate
            # This needs a more robust date parsing utility
            try:
                # Attempt common formats; this is very basic
                parsed_date = None
                # Try DD/MM/YYYY and YYYY/MM/DD first, then MM/DD/YYYY to resolve ambiguity for dates like 01/02/2023
                # For 15/03/2023 (DD/MM) or 03/15/2023 (MM/DD)
                # If it's 03/15/2023, %d/%m/%Y will fail (month 15), then %m/%d/%Y should catch it.
                # If it's 15/03/2023, %d/%m/%Y will catch it.
                # If it's 01/02/2023, %d/%m/%Y catches as Feb 1st. If we want Jan 2nd, MM/DD formats need priority or context.
                # For now, this order is a reasonable compromise.
                date_formats_to_try = (
                    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", # DD/MM/YYYY
                    "%Y/%m/%d", "%Y-%m-%d",             # YYYY/MM/DD
                    "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", # MM/DD/YYYY
                    "%d/%m/%y", "%d-%m-%y", "%d.%m.%y", # DD/MM/YY
                    "%Y/%m/%d", "%Y-%m-%d",             # YYYY/MM/DD (already listed, but ok)
                    "%m/%d/%y", "%m-%d-%y", "%m.%d.%y"  # MM/DD/YY
                )
                for fmt in date_formats_to_try:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                if parsed_date:
                    found_dates.append(parsed_date.strftime("%Y-%m-%d"))
            except ValueError:
                # Could not parse date_str with common formats
                pass

    if found_dates:
        # Assuming the earliest date is the invoice date, or the most prominent one.
        # This logic needs to be smarter (e.g. look for keywords like "Date de facture")
        # For now, just take the first one found that looks like a plausible invoice date.
        # Sorting might help if multiple dates are found to pick earliest/latest.
        extracted_data["invoice_date"] = found_dates[0]


    # Find total amount
    # Search in reverse order of lines as total is often at the bottom
    for line in reversed(lines):
        match_total = total_amount_pattern.search(line)
        if match_total:
            amount_str = match_total.group(1).strip()
            # Clean the amount string (remove spaces, use . as decimal separator)
            amount_str = amount_str.replace(',', '.').replace(' ', '')
            # The following re.sub was causing issues for amounts like "1,234.56" (becoming "1.234.56" then "234.56")
            # It's better to let the robust parsing below handle it or refine this significantly.
            # For now, removing it to test the parsing logic directly on "1.234.56" (post comma replacement)
            # amount_str = re.sub(r'[^\d.]', '', amount_str.split('.')[-2] + '.' + amount_str.split('.')[-1] if '.' in amount_str else amount_str)

            try:
                # Attempt to find the last period as decimal separator
                if '.' in amount_str:
                    parts = amount_str.split('.')
                    if len(parts) > 2 and len(parts[-1]) == 2: # e.g. "1.234.56" from "1,234.56" -> parts=["1","234","56"]
                        integer_part = "".join(parts[:-1]) # "1234"
                        amount_float = float(integer_part + '.' + parts[-1]) # "1234.56"
                    elif len(parts) == 2 and len(parts[-1]) == 2: # e.g. "1234.56" -> parts=["1234","56"]
                        amount_float = float(parts[0] + '.' + parts[1])
                    elif len(parts) == 1 and parts[0] == amount_str : # No dots, e.g. "1234"
                        amount_float = float(amount_str)
                    else: # Fallback or unhandled format with dots
                        amount_float = float(amount_str.replace('.', '')) # simple remove, might be wrong
                else:
                    amount_float = float(amount_str)

                extracted_data["total_amount"] = amount_float
                # Try to infer currency (very basic)
                if "€" in line or "EUR" in line.upper():
                    extracted_data["currency"] = "EUR"
                elif "$" in line or "USD" in line.upper():
                    extracted_data["currency"] = "USD"
                elif "£" in line or "GBP" in line.upper():
                    extracted_data["currency"] = "GBP"
                elif "XOF" in line.upper() or "CFA" in line.upper(): # For user's context
                    extracted_data["currency"] = "XOF"
                break # Found total, stop searching
            except ValueError:
                # print(f"Could not parse amount: {amount_str}")
                pass # Could not convert to float

    return extracted_data

def process_invoice_image(image_path):
    """
    Main function to process an invoice image:
    1. Extract text using OCR.
    2. Parse the text to find relevant information.
    """
    print(f"Processing invoice: {image_path}")
    raw_text = extract_text_from_image(image_path)

    if raw_text:
        print("\n--- Extracted Raw Text ---")
        print(raw_text[:1000]) # Print first 1000 chars for brevity
        print("--------------------------\n")

        parsed_data = parse_extracted_text(raw_text)
        parsed_data['raw_text'] = raw_text # Include raw text for storage

        print("--- Parsed Data ---")
        for key, value in parsed_data.items():
            if key != 'raw_text':
                print(f"{key}: {value}")
        print("-------------------\n")
        return parsed_data
    else:
        print("Could not extract text from image.")
        return None

if __name__ == '__main__':
    # This is for testing the OCR processor directly.
    # You'll need to create a dummy invoice image or use a real one.
    # For example, create 'dummy_invoice.png' in the project root or provide a path.

    # Create a dummy image for testing if no image is provided
    from PIL import Image, ImageDraw, ImageFont
    import os

    dummy_image_path = "dummy_invoice_test.png"

    if not os.path.exists(dummy_image_path):
        try:
            img = Image.new('RGB', (800, 1000), color = (255, 255, 255))
            d = ImageDraw.Draw(img)

            # Attempt to load a font, fallback to default if not found
            try:
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Common on Linux
                if not os.path.exists(font_path):
                    font_path = "arial.ttf" # Common on Windows, might not be on sandbox
                title_font = ImageFont.truetype(font_path, 30)
                text_font = ImageFont.truetype(font_path, 20)
            except IOError:
                print("Default font not found, using PIL's default font. Text might look basic.")
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()

            d.text((50,50), "SUPER FOURNISSEUR SARL", fill=(0,0,0), font=title_font)
            d.text((50,100), "123 Rue de la Facture, 75001 Paris", fill=(0,0,0), font=text_font)
            d.text((50,150), "Facture N°: INV2023-001", fill=(0,0,0), font=text_font)
            d.text((50,200), "Date de facture: 25/10/2023", fill=(0,0,0), font=text_font)
            d.text((50,250), "Échéance: 24/11/2023", fill=(0,0,0), font=text_font)

            d.text((50,350), "Description", fill=(0,0,0), font=text_font)
            d.text((400,350), "Montant", fill=(0,0,0), font=text_font)
            d.text((50,400), "Service de Consultation Alpha", fill=(0,0,0), font=text_font)
            d.text((400,400), "1,250.75", fill=(0,0,0), font=text_font)
            d.text((50,450), "Produit Beta", fill=(0,0,0), font=text_font)
            d.text((400,450), "300.00", fill=(0,0,0), font=text_font)

            d.text((50,600), "Sous-total: 1550.75", fill=(0,0,0), font=text_font)
            d.text((50,650), "TVA (20%): 310.15", fill=(0,0,0), font=text_font)
            d.text((50,700), "Total TTC: 1860.90 EUR", fill=(0,0,0), font=title_font)

            img.save(dummy_image_path)
            print(f"Created dummy invoice image: {dummy_image_path}")
            test_image_path = dummy_image_path
        except Exception as e:
            print(f"Could not create dummy image: {e}")
            print("Please provide a path to an invoice image for testing.")
            test_image_path = None # Or path to a default test image if available
    else:
        test_image_path = dummy_image_path
        print(f"Using existing dummy invoice image: {dummy_image_path}")

    if test_image_path and os.path.exists(test_image_path):
        print(f"\nTesting OCR with: {test_image_path}")
        extracted_data = process_invoice_image(test_image_path)
        if extracted_data:
            # Further actions like saving to DB would go here in a real app
            pass
    elif test_image_path: # Path provided but file does not exist
        print(f"Test image specified but not found: {test_image_path}")
    else: # No image could be created or found
        print("Skipping OCR test as no image is available.")
