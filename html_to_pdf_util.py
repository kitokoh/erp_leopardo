import os
import re # Added re import
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
        The value found, or an empty string if not found or path is invalid.
    """
    if key.startswith("this.") and current_item is not None:
        # Resolve against current_item
        actual_key = key[5:] # Remove "this."
        if isinstance(current_item, dict):
            return current_item.get(actual_key, "")
        # If current_item is not a dict, "this" access might not be meaningful in this simple form
        # For direct access to item if it's not a dict (e.g. list of strings), key could be "this"
        elif actual_key == "": # refers to the item itself if it's a simple type like string
             return current_item
        return "" # "this" used but current_item is not a dict or key is complex for non-dict item

    # Resolve against main context_dict
    parts = key.split('.')
    value = context_dict
    try:
        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            # Handle list index access if needed, e.g. "products.0.name" - not implemented for simplicity
            # elif isinstance(value, list) and part.isdigit():
            #     value = value[int(part)]
            else: # Path is invalid (trying to access subkey on a non-dict)
                return ""
        return value if value is not None else ""
    except (KeyError, TypeError, IndexError):
        return "" # Key not found or invalid access

def render_html_template(template_string: str, context: dict) -> str:
    """
    Renders an HTML template string with data from a context dictionary,
    supporting simple placeholders, conditional blocks, and loops.
    """
    import logging # Added for logging
    logging.debug(f"render_html_template: Called with context keys: {list(context.keys()) if isinstance(context, dict) else 'Non-dict context'}")
    # logging.debug(f"render_html_template: Template content (first 100 chars): {template_string[:100]}")
    try:
        processed_template = template_string

        # 1. Process loops {{#each array_key}}...{{/each}}
        def process_loop(match_obj):
            array_key = match_obj.group(1).strip()
            loop_content_template = match_obj.group(2)
            logging.debug(f"render_html_template: Processing #each loop for key: '{array_key}'")

            array_data = get_value_from_context(array_key, context)
            rendered_loop_items = []

            if isinstance(array_data, list):
                logging.debug(f"render_html_template: Loop key '{array_key}' resolved to list with {len(array_data)} items.")
                for i, item in enumerate(array_data):
                    logging.debug(f"render_html_template: Loop item {i} for key '{array_key}'. Item data (first 100 chars): {str(item)[:100]}")
                    item_specific_content = re.sub(r'\{\{([^}]+?)\}\}',
                                                   lambda m: str(get_value_from_context(m.group(1).strip(), context, item)),
                                                   loop_content_template)
                    rendered_loop_items.append(render_html_template(item_specific_content, context)) # Recursive call
            else:
                logging.warning(f"render_html_template: Loop key '{array_key}' did not resolve to a list. Resolved to type: {type(array_data)}. Loop will be empty.")
            return "".join(rendered_loop_items)

        processed_template = re.sub(r'\{\{#each ([^}]+?)\}\}(.*?)\{\{/each\}\}', process_loop, processed_template, flags=re.DOTALL)

        # 2. Process conditionals {{#if key}}...{{/if}}
        def process_conditional(match_obj):
            condition_key = match_obj.group(1).strip()
            content_if_true = match_obj.group(2)
            logging.debug(f"render_html_template: Processing #if conditional for key: '{condition_key}'")

            value = get_value_from_context(condition_key, context)
            logging.debug(f"render_html_template: Conditional key '{condition_key}' resolved to value: '{str(value)[:100]}' (type: {type(value)})")

            is_truthy = False
            if isinstance(value, bool): is_truthy = value
            elif isinstance(value, (int, float)): is_truthy = value != 0
            elif isinstance(value, (str, list, dict)): is_truthy = len(value) > 0

            logging.debug(f"render_html_template: Conditional key '{condition_key}' truthiness: {is_truthy}")
            if is_truthy:
                return render_html_template(content_if_true, context) # Recursive call
            else:
                return ""

        processed_template = re.sub(r'\{\{#if ([^}]+?)\}\}(.*?)\{\{/if\}\}', process_conditional, processed_template, flags=re.DOTALL)

        # 3. Process simple placeholders {{key.subkey}}
        def replace_placeholder(match):
            key = match.group(1).strip()
            # Log the key being accessed
            # logging.debug(f"render_html_template: Attempting to replace placeholder for key: '{key}'")
            val = get_value_from_context(key, context)
            # Log the value found (or empty string if not found)
            # logging.debug(f"render_html_template: Key '{key}' resolved to value (first 50 chars): '{str(val)[:50]}'")
            return str(val)

        processed_template = re.sub(r'\{\{([^}]+?)\}\}', replace_placeholder, processed_template)

        logging.debug("render_html_template: Finished processing template successfully.")
        return processed_template
    except Exception as e_render:
        logging.error(f"render_html_template: Unhandled exception during rendering: {e_render}", exc_info=True)
        # It's crucial that this exception is caught by the caller, HtmlEditor.populate_html_content,
        # which then returns the original template string. Re-raising is correct here.
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
