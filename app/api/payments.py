from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime # datetime import added for completeness, though not directly used in type hints here

# Assuming models.py is in the same directory as this payments.py file (e.g. /api/payments.py and /api/models.py)
# If payments.py is in /api/ and models.py is in /api/
from . import models # Corrected based on typical FastAPI structure if main.py is above 'api'
# If invoices_crud.py is in /db/cruds/ and this file is in /api/
# The path would be from ..db.cruds import invoices_crud
from app.db.cruds.invoices import invoices_crud


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=models.Invoice, status_code=201)
async def create_invoice(invoice_data: models.InvoiceCreate):
    """
    Create a new invoice.
    """
    # Validate that dates are correctly formatted if necessary, Pydantic handles this for date objects
    # invoice_data_dict = invoice_data.dict() # Pydantic v1
    invoice_data_dict = invoice_data.model_dump() # Pydantic v2

    new_invoice_id = invoices_crud.add_invoice(invoice_data_dict)
    if not new_invoice_id:
        raise HTTPException(status_code=500, detail="Failed to create invoice.")

    created_invoice = invoices_crud.get_invoice_by_id(new_invoice_id)
    if not created_invoice:
        # This case should ideally not happen if add_invoice succeeded and returned an ID
        raise HTTPException(status_code=500, detail="Invoice created but could not be retrieved.")
    return created_invoice

@router.get("/{invoice_id}", response_model=models.Invoice)
async def get_invoice(invoice_id: str = Path(..., title="The ID of the invoice to get")):
    """
    Retrieve a specific invoice by its ID.
    """
    invoice = invoices_crud.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.get("/", response_model=List[models.Invoice])
async def list_invoices(
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    issue_date_start: Optional[date] = Query(None, description="Filter by issue date start"),
    issue_date_end: Optional[date] = Query(None, description="Filter by issue date end"),
    due_date_start: Optional[date] = Query(None, description="Filter by due date start"),
    due_date_end: Optional[date] = Query(None, description="Filter by due date end"),
    sort_by: Optional[str] = Query(None, description="Sort by fields: issue_date, due_date, total_amount, payment_status. Add _asc or _desc for direction, e.g., issue_date_desc"),
    limit: int = Query(100, ge=1, le=1000, description="Number of invoices to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    List all invoices with optional filtering, sorting, and pagination.
    """
    filters = {}
    if payment_status:
        filters['payment_status'] = payment_status
    if client_id:
        filters['client_id'] = client_id
    if project_id:
        filters['project_id'] = project_id
    if issue_date_start:
        filters['issue_date_start'] = issue_date_start.isoformat() if issue_date_start else None
    if issue_date_end:
        filters['issue_date_end'] = issue_date_end.isoformat() if issue_date_end else None
    if due_date_start:
        filters['due_date_start'] = due_date_start.isoformat() if due_date_start else None
    if due_date_end:
        filters['due_date_end'] = due_date_end.isoformat() if due_date_end else None

    invoices = invoices_crud.list_all_invoices(
        filters=filters if filters else None,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )
    return invoices

@router.put("/{invoice_id}", response_model=models.Invoice)
async def update_invoice_details(
    invoice_id: str,
    invoice_update_data: models.InvoiceUpdate
):
    """
    Update an existing invoice.
    """
    # update_data_dict = invoice_update_data.dict(exclude_unset=True) # Pydantic v1
    update_data_dict = invoice_update_data.model_dump(exclude_unset=True) # Pydantic v2

    if not update_data_dict:
        raise HTTPException(status_code=400, detail="No update data provided.")

    success = invoices_crud.update_invoice(invoice_id, update_data_dict)
    if not success:
        # Check if invoice exists first to give a more specific error
        existing_invoice = invoices_crud.get_invoice_by_id(invoice_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        raise HTTPException(status_code=500, detail="Failed to update invoice or no changes made.")

    updated_invoice = invoices_crud.get_invoice_by_id(invoice_id)
    if not updated_invoice:
         # This case should ideally not happen if update_invoice succeeded
        raise HTTPException(status_code=404, detail="Invoice updated but could not be retrieved.")
    return updated_invoice

@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice_record(invoice_id: str):
    """
    Delete an invoice.
    """
    success = invoices_crud.delete_invoice(invoice_id)
    if not success:
        # Check if invoice exists first to give a more specific error
        existing_invoice = invoices_crud.get_invoice_by_id(invoice_id)
        if not existing_invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        raise HTTPException(status_code=500, detail="Failed to delete invoice.")
    return None # FastAPI will return 204 No Content

@router.get("/client/{client_id}", response_model=List[models.Invoice])
async def list_invoices_for_client(client_id: str = Path(..., title="Client ID")):
    """
    Get all invoices associated with a specific client ID.
    """
    invoices = invoices_crud.get_invoices_by_client_id(client_id)
    # No need to raise 404 if list is empty, an empty list is a valid response.
    return invoices

@router.get("/project/{project_id}", response_model=List[models.Invoice])
async def list_invoices_for_project(project_id: str = Path(..., title="Project ID")):
    """
    Get all invoices associated with a specific project ID.
    """
    invoices = invoices_crud.get_invoices_by_project_id(project_id)
    # No need to raise 404 if list is empty, an empty list is a valid response.
    return invoices

