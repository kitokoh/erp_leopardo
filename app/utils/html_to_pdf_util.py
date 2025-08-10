import os
import re # Added re import
import logging

# Basic logging configuration to ensure it's initialized
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Create logger instance at module level

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
    # Ensure the module-level logger is used. This line should already be commented out or removed.
    # logger = logging.getLogger(__name__)
    logger.debug(f"get_value_from_context: Attempting to get key='{key}'")

    if key.startswith("this.") and current_item is not None:
        actual_key = key[5:]
        logger.debug(f"get_value_from_context: 'this.' context. actual_key='{actual_key}', current_item type: {type(current_item)}")
        if isinstance(current_item, dict):
            value = current_item.get(actual_key, "")
            logger.debug(f"get_value_from_context: 'this.' dict access. Value for '{actual_key}': '{str(value)[:100]}'")
            return value
        elif actual_key == "":
             logger.debug(f"get_value_from_context: 'this.' direct item access. Value: '{str(current_item)[:100]}'")
             return current_item
        logger.debug(f"get_value_from_context: 'this.' context but not dict or direct access. Returning empty string.")
        return ""

    parts = key.split('.')
    value = context_dict
    logger.debug(f"get_value_from_context: Main context. Parts: {parts}")
    try:
        for i, part in enumerate(parts):
            if isinstance(value, dict):
                value = value[part]
                logger.debug(f"get_value_from_context: Part {i+1} ('{part}') resolved. Current value type: {type(value)}, value snippet: '{str(value)[:100]}'")
            else:
                logger.debug(f"get_value_from_context: Path invalid at part '{part}'. Current value is not a dict (type: {type(value)}). Returning empty string.")
                return ""
        final_value = value if value is not None else ""
        logger.debug(f"get_value_from_context: Successfully resolved key '{key}'. Final value snippet: '{str(final_value)[:100]}'")
        return final_value
    except (KeyError, TypeError, IndexError) as e_resolve:
        logger.debug(f"get_value_from_context: Failed to resolve key '{key}' at part '{part}'. Error: {e_resolve}. Returning empty string.")
        return ""

def render_html_template(template_string: str, context: dict) -> str:
    """
    Renders an HTML template string with data from a context dictionary,
    supporting simple placeholders, conditional blocks, and loops.
    """
    # Ensure logger is configured if not already done globally
    # logging.basicConfig(level=logging.DEBUG) # Basic config if needed
    # Ensure the module-level logger is used. This line should already be commented out or removed.
    # logger = logging.getLogger(__name__)

    logger.debug(f"render_html_template: START. Context keys: {list(context.keys()) if isinstance(context, dict) else 'Non-dict context'}")
    # For very detailed debugging, print small parts of context:
    # if isinstance(context, dict):
    #     logger.debug(f"Context[doc] sample: {str(context.get('doc', {}))[:200]}")
    #     logger.debug(f"Context[client] sample: {str(context.get('client', {}))[:200]}")
    #     logger.debug(f"Context[seller] sample: {str(context.get('seller', {}))[:200]}")
    # logger.debug(f"render_html_template: Template content (first 200 chars): {template_string[:200]}")

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

        # 3. Process simple placeholders {{key.subkey}} or {{key.subkey | default('fallback')}}
        def replace_placeholder(match_obj):
            full_key_expression = match_obj.group(1).strip()

            key_parts = full_key_expression.split('|', 1)
            actual_key = key_parts[0].strip()
            default_value_provided = None
            use_default = False

            if len(key_parts) > 1:
                default_part = key_parts[1].strip()
                # Regex to capture content inside default('...') or default("...")
                default_match = re.match(r"default\s*\(\s*['\"](.*?)['\"]\s*\)", default_part)
                if default_match:
                    default_value_provided = default_match.group(1)
                else:
                    # If pattern is not default('string') or default("string"), log warning or handle differently.
                    # For now, we assume if there's a pipe, it's intended for default, and if not matching, the default part is invalid.
                    logger.warning(f"render_html_template: Found '|' but default syntax not recognized: '{default_part}'. Key: '{actual_key}'")
                    # In this case, we will just try to render actual_key and ignore the malformed default part.

            # Log for special keys (debugging aid)
            if actual_key in ["main_image_path", "seller.logo_url", "doc.logo_path"]:
                logger.info(f"render_html_template (replace_placeholder): Processing key='{actual_key}'")
            else:
                logger.debug(f"render_html_template (replace_placeholder): Processing key='{actual_key}'")

            val = get_value_from_context(actual_key, context) # context is accessible due to nested function scope

            # Condition to use default: if val is empty string (primary indicator of not found/None from get_value_from_context)
            # AND a default value was successfully parsed.
            if val == "" and default_value_provided is not None:
                logger.debug(f"render_html_template (replace_placeholder): Key '{actual_key}' resolved to empty. Using provided default: '{default_value_provided}'")
                val = default_value_provided # Use the parsed default value
                use_default = True

            if not use_default:
                if actual_key in ["main_image_path", "seller.logo_url", "doc.logo_path"]:
                    logger.info(f"render_html_template (replace_placeholder): Value for key='{actual_key}': '{str(val)[:200]}'")
                else:
                    logger.debug(f"render_html_template (replace_placeholder): Value for key='{actual_key}': '{str(val)[:100]}'")

            return str(val)

        processed_template = re.sub(r'\{\{\s*(.*?)\s*\}\}', replace_placeholder, processed_template)

        # Debugging check for remaining placeholders (can be removed in production)
        # remaining_placeholders = re.findall(r'\{\{.*?\}\}', processed_template)
        # if remaining_placeholders:
        #     logger.warning(f"render_html_template: Found remaining placeholders after processing: {remaining_placeholders[:5]}")
        #     if "{{ main_image_path }}" in processed_template or "{{ seller.logo_url }}" in processed_template:
        #         logger.warning("render_html_template: Placeholders for main_image_path or seller.logo_url still exist in processed_template before returning!")
        #         logger.debug(f"Problematic template snippet (around main_image_path): {processed_template[max(0, processed_template.find('main_image_path')-20):processed_template.find('main_image_path')+40]}")
        #         logger.debug(f"Problematic template snippet (around seller.logo_url): {processed_template[max(0, processed_template.find('seller.logo_url')-20):processed_template.find('seller.logo_url')+40]}")

        logger.debug("render_html_template: FINISHED processing template successfully.")
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
