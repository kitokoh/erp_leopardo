import os
import logging

# Assuming context_builder is in the same package
from .context_builder import get_document_context

# Assuming html_to_pdf_util.py is in the parent directory of the document_generator package
# Adjust the import path if html_to_pdf_util.py is located elsewhere.
# For example, if it's a top-level module: from html_to_pdf_util import ...
# If it's a utility module within document_generator: from .html_to_pdf_util import ...
try:
    from ..html_to_pdf_util import render_html_template, convert_html_to_pdf
except ImportError:
    # Fallback if running directly or if structure is different, try direct import
    # This might happen if document_generator is not run as part of a package
    # or if html_to_pdf_util is in the same directory (though less likely for a util)
    try:
        import html_to_pdf_util
        render_html_template = html_to_pdf_util.render_html_template
        convert_html_to_pdf = html_to_pdf_util.convert_html_to_pdf
    except ImportError:
        logging.error(
            "Failed to import html_to_pdf_util. Ensure it's accessible. "
            "render_html_template and convert_html_to_pdf will not be available."
        )
        # Define dummy functions if import fails, to allow module to load for other purposes
        # but these will not work.
        def render_html_template(template_content, context):
            raise NotImplementedError("html_to_pdf_util.render_html_template not imported")

        def convert_html_to_pdf(html_content, base_url=None):
            raise NotImplementedError("html_to_pdf_util.convert_html_to_pdf not imported")


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_html_document(
    client_id: int,
    company_id: int,
    template_path: str,
    language_code: str,
    project_id: int = None,
    document_type: str = None, # Added to pass to get_document_context
    additional_context: dict = None,
    db_conn=None,
    app_root_dir: str = None, # Added app_root_dir
    _test_force_context: dict = None # Added for testing
) -> str | None:
    """
    Generates an HTML document by fetching context and rendering a template.

    Args:
        client_id: ID of the client.
        company_id: ID of the seller company.
        template_path: Absolute path to the HTML template file.
        language_code: Language code for translations.
        project_id: Optional ID of the project.
        document_type: Optional type of document (e.g. 'proforma_invoice') for context.
        additional_context: Optional dictionary for overrides or extra information
                              to be passed to get_document_context.
        db_conn: Optional existing database connection.

    Returns:
        The generated HTML content as a string, or None on failure.
    """
    if not os.path.exists(template_path):
        logger.error(f"HTML template not found at: {template_path}")
        return None

    if additional_context is None:
        additional_context = {}

    # Ensure document_type from additional_context is also passed to get_document_context
    # if not directly provided as a parameter.
    effective_document_type = document_type or additional_context.get('document_type')


    logger.info(f"Generating HTML document: client_id={client_id}, company_id={company_id}, "
                f"template='{os.path.basename(template_path)}', lang='{language_code}', project_id={project_id}")

    try:
        # 1. Fetch document context
        if _test_force_context:
            logger.info("Using _test_force_context")
            context = _test_force_context
        else:
            context = get_document_context(
                client_id=client_id,
                company_id=company_id,
            language_code=language_code,
            project_id=project_id,
            document_type=effective_document_type, # Pass it here
            additional_data=additional_context,
            db_conn=db_conn,
            app_root_dir=app_root_dir # Pass app_root_dir
        )
        if not context:
            logger.error("Failed to retrieve document context.")
            return None

        # 2. Read HTML template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 3. Render HTML template
        # Assuming render_html_template is a Jinja2 based renderer
        # It should take the template string and the context dictionary
        html_output = render_html_template(template_content, context)
        if not html_output:
            logger.error("HTML template rendering failed. render_html_template returned empty.")
            return None

        logger.info("HTML document generated successfully.")
        return html_output

    except FileNotFoundError:
        logger.error(f"HTML template file not found at: {template_path}")
        return None
    except Exception as e:
        logger.error(f"Error generating HTML document: {e}", exc_info=True)
        return None


def generate_html_and_convert_to_pdf(
    client_id: int,
    company_id: int,
    template_path: str,
    language_code: str,
    output_pdf_path: str,
    project_id: int = None,
    document_type: str = None, # Added to pass to generate_html_document
    additional_context: dict = None,
    db_conn=None,
    app_root_dir: str = None, # Added app_root_dir
    _test_force_context: dict = None # Added for testing
) -> bool:
    """
    Generates an HTML document, converts it to PDF, and saves it.

    Args:
        client_id: ID of the client.
        company_id: ID of the seller company.
        template_path: Absolute path to the HTML template file.
        language_code: Language code for translations.
        output_pdf_path: Path where the generated PDF should be saved.
        project_id: Optional ID of the project.
        document_type: Optional type of document (e.g. 'proforma_invoice') for context.
        additional_context: Optional dictionary for overrides or extra information.
        db_conn: Optional existing database connection.

    Returns:
        True on success, False on failure.
    """
    logger.info(f"Starting PDF generation: client_id={client_id}, company_id={company_id}, "
                f"template='{os.path.basename(template_path)}', output='{output_pdf_path}'")

    # 1. Generate HTML content
    html_content = generate_html_document(
        client_id=client_id,
        company_id=company_id,
        template_path=template_path,
        language_code=language_code,
        project_id=project_id,
        document_type=document_type,
        additional_context=additional_context,
        db_conn=db_conn,
        app_root_dir=app_root_dir, # Pass app_root_dir
        _test_force_context=_test_force_context # Pass through
    )

    if not html_content:
        logger.error("HTML generation failed, cannot proceed to PDF conversion.")
        return False

    try:
        # 2. Determine base_url for PDF conversion (for relative assets)
        # The base_url should point to the directory containing the template,
        # so that relative paths to CSS, images, etc., in the HTML are resolved.
        base_url = os.path.dirname(template_path)
        # For WeasyPrint, local paths need to be in file:// URI form
        if not base_url.startswith('file://'):
             base_url = f"file://{base_url}/"


        # 3. Convert HTML to PDF
        # convert_html_to_pdf should take HTML string and base_url, return PDF bytes
        pdf_bytes = convert_html_to_pdf(html_content, base_url=base_url)

        if not pdf_bytes:
            logger.error("PDF conversion failed. convert_html_to_pdf returned empty.")
            return False

        # 4. Save PDF to output_pdf_path
        output_dir = os.path.dirname(output_pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")

        with open(output_pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        logger.info(f"PDF successfully generated and saved to: {output_pdf_path}")
        return True

    except Exception as e:
        logger.error(f"Error during PDF generation or saving: {e}", exc_info=True)
        return False


# The get_document_context is imported at the top of the file as:
# from .context_builder import get_document_context
# We will patch this imported name directly in the __main__ block.

if __name__ == '__main__':
    logger.info("Starting HTML generator test run for contact_page_template.html...")

if __name__ == '__main__':
    logger.info("Starting HTML generator test run for contact_page_template.html...")

    # Define the mock context directly
    mock_contacts_data = [
        {"organization_name": "Client Corp SARL", "name": "Jean Dupont", "position": "Directeur Technique", "email": "jean.dupont@clientcorp.com", "phone": "01 23 45 67 89"},
        {"organization_name": "Client Corp SARL", "name": "Marie Curie", "position": "Chef de Projet", "email": "marie.curie@clientcorp.com", "phone": "01 23 45 67 80"},
        {"organization_name": "Partenaire XYZ", "name": "Pierre Martin", "position": "Consultant Externe", "email": "pierre.martin@partenaire.xyz", "phone": "06 00 00 00 00"}
    ]

    forced_test_context = {
        "doc": {"current_date_formatted": "15/07/2024"},
        "client": {},
        "seller": {"name": "Ma Super Entreprise ( vendeur )", "logo_url": "file:///example_logo.png"},
        "project": {"id": "PROJ789", "identifier": "P789-Alpha", "name": "Grand Projet de Rénovation Urbaine"},
        "contacts_list": mock_contacts_data,
        "contacts_list_empty": not bool(mock_contacts_data),
        "lang": {"code": "fr", "text_direction": "ltr"},
        "placeholders": {
            "PROJECT_ID": "PROJ789-Placeholder",
            "PROJECT_NAME_CONTACT_PAGE": "Grand Projet de Rénovation Urbaine (via placeholder)",
            "DATE_CONTACT_PAGE": "15/07/2024 (via placeholder)",
            "SELLER_COMPANY_NAME": "Ma Super Entreprise SARL (via placeholder)",
            "SELLER_LOGO_PATH": "file:///example_logo.png"
        },
        "labels": {},
        "additional": {"custom_info": "Test Value"}
    }

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    contact_template_path = os.path.join(project_root, "templates", "fr", "contact_page_template.html")
    output_pdf_file = "contact_page_generated.pdf"

    logger.info(f"Attempting to generate PDF from template: {contact_template_path}")
    if not os.path.exists(contact_template_path):
        logger.error(f"Template file not found: {contact_template_path}. Current dir: {os.getcwd()}")
        exit(1)

    pdf_success = generate_html_and_convert_to_pdf(
        client_id=1,
        company_id=1,
        template_path=contact_template_path,
        language_code='fr',
        output_pdf_path=output_pdf_file,
        project_id=789,
        document_type='contact_page',
        additional_context={"custom_info": "Test Value from additional_context"}, # This will be in context.additional
        app_root_dir=project_root,
        _test_force_context=forced_test_context # Pass the forced context
    )

    if pdf_success:
        logger.info(f"PDF generation successful! Output at: {os.path.abspath(output_pdf_file)}")
    else:
        logger.error("PDF generation failed.")

    logger.info("HTML generator test run for contact_page_template.html finished.")
