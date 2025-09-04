import logging
from app.db.cruds.clients import clients_crud
from app.db.cruds.projects import projects_crud
from app.db.cruds.products import products_crud as products_crud_module
from app.db.cruds.misc import locations_crud
from app.db.cruds.clients import client_project_products_crud
from app.db.cruds.invoices import proforma_invoices_crud

# Note: Caching is removed during this refactoring to ensure stability.
# It can be re-introduced later with a more robust session-aware strategy.

def fetch_global_stats(db_session, start_date, end_date):
    """Fetches a dictionary of global statistics."""
    try:
        current_total_clients = clients_crud.get_total_clients_count(db_session)
        current_active_clients = clients_crud.get_active_clients_count(db_session)
        total_projects = projects_crud.get_total_projects_count(db_session)
        active_projects = projects_crud.get_active_projects_count(db_session)
        total_products = products_crud_module.get_total_products_count(db_session)
        sales_in_period = get_total_sales_from_proforma(db_session, start_date, end_date)

        return {
            "total_clients": current_total_clients,
            "active_clients": current_active_clients,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_products": total_products,
            "sales_in_period": sales_in_period,
        }
    except Exception as e:
        logging.error(f"Error in fetch_global_stats: {e}", exc_info=True)
        return {
            "total_clients": 0, "active_clients": 0, "total_projects": 0,
            "active_projects": 0, "total_products": 0, "sales_in_period": 0.0,
        }

def get_total_sales_from_proforma(db_session, start_date, end_date) -> float:
    """Calculates total sales from proforma invoices for a given period."""
    try:
        start_iso = start_date.toString("yyyy-MM-dd") + "T00:00:00.000000Z"
        end_iso = end_date.toString("yyyy-MM-dd") + "T23:59:59.999999Z"
        total_sales = proforma_invoices_crud.get_total_sales_amount_for_period(db_session, start_iso, end_iso)
        return total_sales
    except Exception as e:
        logging.error(f"Error calculating total sales from proforma: {e}", exc_info=True)
        return 0.0

def get_country_stats(db_session, country_name):
    """Fetches statistics for a specific country."""
    try:
        country_obj = locations_crud.get_country_by_name(db_session, country_name)
        if not country_obj:
            logging.error(f"Country '{country_name}' not found in DB.")
            return None

        country_id = country_obj['country_id']
        client_count = clients_crud.get_client_count_by_country_id(db_session, country_id=country_id, include_deleted=False)
        project_count = projects_crud.get_active_project_count_by_country_id(db_session, country_id=country_id)
        sales_value = proforma_invoices_crud.get_total_proforma_sales_for_country_id(db_session, country_id=country_id)

        return {
            "client_count": client_count,
            "project_count": project_count,
            "sales_value": sales_value,
            "country_obj": country_obj
        }
    except Exception as e:
        logging.error(f"Error in get_country_stats for {country_name}: {e}", exc_info=True)
        return None

def get_client_counts_by_country(db_session):
    return clients_crud.get_client_counts_by_country(db_session)

def get_client_segmentation_by_city(db_session):
    return clients_crud.get_client_segmentation_by_city(db_session)

def get_client_segmentation_by_status(db_session):
    return clients_crud.get_client_segmentation_by_status(db_session)

def get_client_segmentation_by_category(db_session):
    return clients_crud.get_client_segmentation_by_category(db_session)

def get_product_usage_counts(db_session):
    return client_project_products_crud.get_product_usage_counts(db_session)

def get_total_clients_count(db_session):
    return clients_crud.get_total_clients_count(db_session)

def get_active_clients_count(db_session):
    return clients_crud.get_active_clients_count(db_session)

def get_active_projects_count(db_session):
    return projects_crud.get_active_projects_count(db_session)

def get_total_sales_amount_for_period(db_session, start_date, end_date):
    return proforma_invoices_crud.get_total_sales_amount_for_period(db_session, start_date, end_date)
