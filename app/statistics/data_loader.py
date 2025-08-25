import logging
from cachetools import cached
from .cache import cache
from app.db.cruds.clients.clients_crud import (
    get_total_clients_count,
    get_active_clients_count,
    get_client_counts_by_country,
    get_client_segmentation_by_status,
    get_client_segmentation_by_category,
    get_client_segmentation_by_city,
)
from app.db.cruds.projects.projects_crud import (
    get_total_projects_count,
    get_active_projects_count,
)
from app.db.cruds.products.products_crud import products_crud_instance as products_crud
from app.db.cruds.misc.locations_crud import get_country_by_name, get_country_by_id, get_city_by_id
from app.db.cruds.misc.status_settings_crud import get_status_setting_by_id, get_status_setting_by_name
from app.db.cruds.clients.clients_crud import clients_crud_instance
from app.db.connection import get_db_connection
from app.db.cruds.clients.client_project_products_crud import get_product_usage_counts
from app.db.cruds.invoices.proforma_invoices_crud import get_total_sales_amount_for_period, get_total_proforma_sales_for_country_id
from app.db.cruds.projects.projects_crud import get_active_project_count_by_country_id

@cached(cache)
def fetch_global_stats(start_date, end_date):
    db_session = None
    try:
        db_session = get_db_connection()
        current_total_clients = get_total_clients_count(db_session)
        current_active_clients = get_active_clients_count(db_session)
        total_projects = get_total_projects_count(db_session)
        active_projects = get_active_projects_count(db_session)
        total_products = products_crud.get_total_products_count(db_session)
        sales_in_period = get_total_sales_from_proforma(start_date, end_date)

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
        return {}
    finally:
        if db_session:
            db_session.close()

@cached(cache)
def get_total_sales_from_proforma(start_date, end_date) -> float:
    db_session = None
    try:
        start_iso = start_date.toString("yyyy-MM-dd") + "T00:00:00.000000Z"
        end_iso = end_date.toString("yyyy-MM-dd") + "T23:59:59.999999Z"
        db_session = get_db_connection()
        total_sales = get_total_sales_amount_for_period(db_session, start_iso, end_iso)
        return total_sales
    except Exception as e:
        logging.error(f"Error calculating total sales from proforma for period: {e}", exc_info=True)
        return 0.0
    finally:
        if db_session:
            try:
                db_session.close()
            except Exception as e_close:
                logging.error(f"Error closing db_session in get_total_sales_from_proforma: {e_close}", exc_info=True)

@cached(cache)
def get_country_stats(db_session, country_name):
    country_obj = get_country_by_name(db_session, country_name)
    if not country_obj:
        logging.error(f"Country '{country_name}' not found in DB.")
        return None

    country_id = country_obj['country_id']
    client_count = clients_crud_instance.get_client_count_by_country_id(db_session, country_id=country_id, include_deleted=False)
    project_count = get_active_project_count_by_country_id(db_session, country_id=country_id)
    sales_value = get_total_proforma_sales_for_country_id(db_session, country_id=country_id)

    return {
        "client_count": client_count,
        "project_count": project_count,
        "sales_value": sales_value,
        "country_obj": country_obj
    }
