import os
import re # Added re import
import logging

# Basic logging configuration to ensure it's initialized
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Create logger instance at module level

from jinja2 import Environment, select_autoescape, FileSystemLoader, BaseLoader, StrictUndefined

from weasyprint import HTML
from weasyprint.urls import URLFetchingError # Corrected import

class WeasyPrintError(Exception):
    """Custom exception for WeasyPrint conversion errors."""
    pass

# def populate_html(template_content: str, data: dict) -> str:
#     """
#     Populates an HTML template string with data from a dictionary.
#
#     Args:
#         template_content: The HTML content as a string with placeholders.
#         data: A dictionary where keys are placeholder names (e.g., "TITLE")
#               and values are the data to insert.
#
#     Returns:
#         The populated HTML string.
#     """
#     populated_html_string = template_content
#     for key, value in data.items():
#         placeholder = f"{{{{{key}}}}}" # e.g. {{TITLE}}
#         populated_html_string = populated_html_string.replace(placeholder, str(value))
#     return populated_html_string

def get_value_from_context(key: str, context_dict: dict, current_item: dict = None) -> any:
    """
    Retrieves a value from a nested context dictionary using a dot-notated key.
    If key starts with "this." and current_item is provided, it resolves against current_item.

    Args:
        key: The dot-notated key (e.g., "client.name", "this.product_name").
        context_dict: The main context dictionary.
        current_item: The current item in a loop (optional).

    Returns:
# The get_value_from_context function is no longer needed with Jinja2.
# It can be removed or kept if used elsewhere, but render_html_template will not use it.


def render_html_template(template_string: str, context: dict) -> str:
    """
    Renders an HTML template string with data from a context dictionary using Jinja2.
    """
    logger.debug(f"render_html_template (Jinja2): START. Context keys: {list(context.keys()) if isinstance(context, dict) else 'Non-dict context'}")

    try:
        # Using StrictUndefined to raise an error for undefined variables in templates,
        # which can help catch issues earlier. Default is Undefined which renders as empty string.
        # autoescape=select_autoescape(['html', 'xml']) is good practice for security if user-generated content might be in templates.
        env = Environment(
            loader=BaseLoader(), # Using BaseLoader as we're loading from a string
            autoescape=select_autoescape(['html', 'xml']),
            undefined=StrictUndefined # Makes it error out on undefined variables
        )

        # Add a custom filter for currency formatting if needed within Jinja templates
        # For example: {{ my_value | currency }}
        # env.filters['currency'] = format_currency # Assuming format_currency is defined elsewhere or in this module

        template = env.from_string(template_string)
        rendered_html = template.render(context)

        logger.debug("render_html_template (Jinja2): FINISHED processing template successfully.")
        return rendered_html
    except StrictUndefined as e_strict:
        logger.error(f"render_html_template (Jinja2): Undefined variable in template. Error: {e_strict}", exc_info=True)
        # Optionally, re-raise or return template_string or a specific error message string.
        # For now, re-raising to make it clear something is missing in the context.
        raise  # Re-raise the StrictUndefined error to make missing variables explicit

    except Exception as e_render:
        logger.error(f"render_html_template (Jinja2): Unhandled exception during rendering: {e_render}", exc_info=True)
        # Re-raise to be caught by the caller (e.g., HtmlEditor.populate_html_content)
        raise


def convert_html_to_pdf(html_string: str, base_url: str = None) -> bytes | None:
    """
    Converts a populated HTML string to PDF bytes using WeasyPrint.

    Args:
        html_string: The populated HTML string to convert.
        base_url: The base URL for resolving relative paths (e.g., for images).
                  This should typically be the directory of the HTML templates.

    Returns:
        The PDF content as bytes if successful, None otherwise.
        Raises WeasyPrintError if WeasyPrint encounters an error during PDF generation.
    """
    try:
        # The base_url is crucial for WeasyPrint to find local resources like images or CSS files
        # that are referenced with relative paths in the HTML.
        return HTML(string=html_string, base_url=base_url).write_pdf()
    except URLFetchingError as e: # Corrected specific exception
        # This specific catch is for URL fetching errors, which might be common
        # if LOGO_PATH is relative and base_url is not set correctly.
        error_message = f"WeasyPrint URL fetching error: {e}. Ensure base_url is set correctly for relative image paths or use absolute URLs for resources."
        # Consider logging this error
        print(error_message) # Or use a proper logger
        raise WeasyPrintError(error_message) from e
    except Exception as e:
        # Catching a general exception for other WeasyPrint errors.
        error_message = f"An error occurred during PDF conversion with WeasyPrint: {e}"
        # Consider logging this error
        print(error_message) # Or use a proper logger
        raise WeasyPrintError(error_message) from e

if __name__ == '__main__':
    # Example Usage (for testing the new render_html_template)

    # 1. Define sample context data (nested structure)
    sample_context = {
        "doc": {
            "title": "Awesome Document 2.0",
            "show_details": True,
            "show_less": False,
            "logo_path": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png" # Example URL
        },
        "client": {
            "name": "Test Client Inc.",
            "address": {
                "street": "123 Main St",
                "city": "Techville"
            }
        },
        "seller": {
            "name": "My Corp Ltd.",
            "contact_person": "Jane Seller"
        },
        "products": [
            {"name": "Super Gadget", "price_formatted": "€10.00", "description": "A very super gadget."},
            {"name": "Mega Widget", "price_formatted": "€20.50", "description": "A mega useful widget."},
            {"name": "Basic Gizmo", "price_formatted": "€5.25", "description": "Your everyday gizmo."}
        ],
        "empty_list": [],
        "notes": "Some final notes here."
    }

    # 2. Create a dummy HTML template string using new features
    dummy_template_html = """
    <!DOCTYPE html>
    <html>
    <head><title>{{doc.title}}</title></head>
    <body>
        <img src="{{doc.logo_path}}" alt="Logo" width="100">
        <h1>{{doc.title}}</h1>
        <p>Client: {{client.name}} from {{client.address.city}}</p>
        <p>Seller: {{seller.name}} (Contact: {{seller.contact_person}})</p>

        {{#if doc.show_details}}
        <h2>Product Details:</h2>
        <ul>
            {{#each products}}
            <li>
                <strong>{{this.name}}</strong> - {{this.price_formatted}}
                <p>{{this.description}}</p>
            </li>
            {{/each}}
        </ul>
        {{/if}}

        {{#if doc.show_less}}
        <p>Showing less details as requested.</p>
        {{/if}}

        <h3>Looping an empty list (should show nothing):</h3>
        <p>Start of empty list section.</p>
        {{#each empty_list}}
        <p>This item from empty_list should not appear: {{this.name}}</p>
        {{/each}}
        <p>End of empty list section.</p>

        <p>Notes: {{notes}}</p>
        <p>Missing value test: {{nonexistent.key}}</p>
        <p>Direct item from list (if list of strings - not in this sample): {{this}}</p>
    </body>
    </html>
    """

    # 3. Render the template
    print("Rendering HTML template with new engine...")
    rendered_content = render_html_template(dummy_template_html, sample_context)
    print("Rendered HTML:")
    print(rendered_content)
    print("-" * 30)

    # 4. Convert to PDF (optional, for further testing)
    print("\nConverting to PDF...")
    pdf_bytes = None
    try:
        pdf_bytes = convert_html_to_pdf(rendered_content, base_url=None) # base_url needed if local relative paths
    except WeasyPrintError as e:
        print(f"PDF Conversion Error: {e}")
    except ImportError:
        print("WeasyPrint is not installed. Please install it to run the PDF conversion example.")

    if pdf_bytes:
        output_pdf_path = "example_output_new_render.pdf"
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF successfully generated with new render engine: {output_pdf_path}")
    else:
        print("PDF generation failed or was skipped (new render engine).")
