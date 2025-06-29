import os
import logging
from jinja2 import Environment, BaseLoader, select_autoescape, StrictUndefined
from weasyprint import HTML
from weasyprint.urls import URLFetchingError

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeasyPrintError(Exception):
    """Custom exception for WeasyPrint conversion errors."""
    pass

def render_html_template(template_string: str, context: dict) -> str:
    """
    Renders an HTML template string with data from a context dictionary using Jinja2.
    """
    logger.debug(f"render_html_template (Jinja2): START. Context keys: {list(context.keys()) if isinstance(context, dict) else 'Non-dict context'}")

    try:
        env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(['html', 'xml']),
            undefined=StrictUndefined
        )
        # Example of adding a custom filter, if needed later:
        # from document_generator.context_builder import format_currency # Assuming format_currency is accessible
        # env.filters['currency'] = format_currency

        template = env.from_string(template_string)
        rendered_html = template.render(context)

        logger.debug("render_html_template (Jinja2): FINISHED processing template successfully.")
        return rendered_html
    except StrictUndefined as e_strict:
        logger.error(f"render_html_template (Jinja2): Undefined variable in template. Error: {e_strict}", exc_info=True)
        raise
    except Exception as e_render:
        logger.error(f"render_html_template (Jinja2): Unhandled exception during rendering: {e_render}", exc_info=True)
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
        return HTML(string=html_string, base_url=base_url).write_pdf()
    except URLFetchingError as e:
        error_message = f"WeasyPrint URL fetching error: {e}. Ensure base_url is set correctly for relative image paths or use absolute URLs for resources."
        logger.error(error_message, exc_info=True)
        raise WeasyPrintError(error_message) from e
    except Exception as e:
        error_message = f"An error occurred during PDF conversion with WeasyPrint: {e}"
        logger.error(error_message, exc_info=True)
        raise WeasyPrintError(error_message) from e

if __name__ == '__main__':
    logger.info("Starting html_to_pdf_util.py self-test...")

    # Simplified test to avoid complex string literals for now
    sample_context_simple = {"name": "World"}
    test_template_simple = "<h1>Hello {{ name }}!</h1>"

    try:
        rendered_simple = render_html_template(test_template_simple, sample_context_simple)
        logger.info(f"Simple render output: {rendered_simple}")

        # Test with a missing variable (should raise StrictUndefined)
        try:
            render_html_template("<h1>Hello {{ undefined_name }}!</h1>", sample_context_simple)
        except StrictUndefined as e_undef:
            logger.info(f"Correctly caught StrictUndefinedError: {e_undef}")
        except Exception as e_other_undef:
            logger.error(f"Unexpected error during undefined variable test: {e_other_undef}")

    except Exception as e:
        logger.error(f"Error during simplified self-test: {e}", exc_info=True)

    logger.info("html_to_pdf_util.py self-test finished.")
# End of html_to_pdf_util.py
