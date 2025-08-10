from .clients_crud import clients_crud_instance
from .client_assigned_personnel_crud import *
from .client_contacts_crud import *
from .client_documents_crud import *
from .client_freight_forwarders_crud import *
from .client_order_money_transfer_agents_crud import (
    assign_agent_to_client_order,
    get_assigned_agents_for_client_order,
    get_assigned_agents_for_client,
    update_assignment_details,
    unassign_agent_from_client_order,
)
from .client_project_products_crud import *
from .client_transporters_crud import *
from .client_visits_crud import *
