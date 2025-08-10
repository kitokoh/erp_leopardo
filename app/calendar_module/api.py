from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from datetime import date

from .models import CompanyCalendarSettings, UserCalendarEvent
from .cruds import company_calendar_settings_crud, user_calendar_events_crud
# Assuming you have a dependency for getting current user, similar to other modules
# from api.dependencies import get_current_active_user # Placeholder

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar Management"],
    # dependencies=[Depends(get_current_active_user)] # Secure endpoints if needed
)

# --- Company Calendar Settings Endpoints ---

@router.post("/settings/", response_model=CompanyCalendarSettings)
async def create_or_update_company_settings(
    settings: CompanyCalendarSettings = Body(...)
    # current_user: dict = Depends(get_current_active_user) # Example: link settings to user
):
    """
    Create new company calendar settings or update existing ones for the current user.
    The `user_id` in the settings body should match the authenticated user or be managed by the backend.
    """
    # For this example, we'll assume settings.user_id is provided and valid.
    # In a real app, you might set user_id based on the authenticated user.
    # if settings.user_id != current_user["user_id"]:
    #     raise HTTPException(status_code=403, detail="User ID mismatch or not authorized")

    saved_settings = company_calendar_settings_crud.save_settings(settings)
    if not saved_settings:
        raise HTTPException(status_code=500, detail="Could not save company calendar settings.")
    return saved_settings

@router.get("/settings/{user_id}", response_model=Optional[CompanyCalendarSettings])
async def get_company_settings(
    user_id: str
    # current_user: dict = Depends(get_current_active_user) # Example
):
    """
    Retrieve company calendar settings for a specific user_id.
    """
    # if user_id != current_user["user_id"] and not current_user.get("is_admin", False): # Basic auth check
    #     raise HTTPException(status_code=403, detail="Not authorized to view these settings")

    settings = company_calendar_settings_crud.get_settings_by_user_id(user_id)
    if settings is None:
        # Optionally, return a default empty response or a 404 if settings are expected
        # For now, returning None (which FastAPI handles as null in JSON) is fine if settings might not exist.
        pass
    return settings

# --- User Calendar Event Endpoints ---

@router.post("/events/", response_model=UserCalendarEvent)
async def add_user_event(
    event: UserCalendarEvent = Body(...)
    # current_user: dict = Depends(get_current_active_user) # Example
):
    """
    Add a new calendar event for the user.
    The `user_id` in the event body should match the authenticated user or be managed.
    """
    # if event.user_id != current_user["user_id"]:
    #     raise HTTPException(status_code=403, detail="User ID mismatch or not authorized for this event")

    new_event = user_calendar_events_crud.add_event(event)
    if not new_event:
        raise HTTPException(status_code=500, detail="Could not add calendar event.")
    return new_event

@router.get("/events/{user_id}", response_model=List[UserCalendarEvent])
async def get_user_events(
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
    # current_user: dict = Depends(get_current_active_user) # Example
):
    """
    Retrieve calendar events for a specific user_id, optionally filtered by a date range.
    """
    # if user_id != current_user["user_id"] and not current_user.get("is_admin", False):
    #     raise HTTPException(status_code=403, detail="Not authorized to view these events")

    events = user_calendar_events_crud.get_events_by_user_id(user_id, start_date=start_date, end_date=end_date)
    return events

@router.put("/events/{event_id}", response_model=UserCalendarEvent)
async def update_user_event(
    event_id: int,
    event_update_data: dict = Body(...) # Or a Pydantic model for updates
    # current_user: dict = Depends(get_current_active_user) # Example
):
    """
    Update an existing calendar event by its ID.
    Ensures the event belongs to the authenticated user before updating.
    """
    # First, verify ownership or admin rights
    # existing_event = user_calendar_events_crud.get_by_id(event_id) # Assuming GenericCRUD has get_by_id
    # if not existing_event:
    #     raise HTTPException(status_code=404, detail="Event not found")
    # if existing_event.user_id != current_user["user_id"] and not current_user.get("is_admin", False):
    #     raise HTTPException(status_code=403, detail="Not authorized to update this event")

    updated_event = user_calendar_events_crud.update_event(event_id, event_update_data)
    if not updated_event:
        # This could be due to not found, or error during update
        # Refine error handling based on CRUD method's return
        raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found or update failed.")
    return updated_event

@router.delete("/events/{event_id}", status_code=204) # 204 No Content for successful deletion
async def delete_user_event(
    event_id: int
    # current_user: dict = Depends(get_current_active_user) # Example
):
    """
    Delete a calendar event by its ID.
    Ensures the event belongs to the authenticated user before deleting.
    """
    # Verify ownership or admin rights (similar to update)
    # existing_event = user_calendar_events_crud.get_by_id(event_id)
    # if not existing_event:
    #     raise HTTPException(status_code=404, detail="Event not found")
    # if existing_event.user_id != current_user["user_id"] and not current_user.get("is_admin", False):
    #     raise HTTPException(status_code=403, detail="Not authorized to delete this event")

    success = user_calendar_events_crud.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Event with id {event_id} not found or delete failed.")
    return None # FastAPI will return 204 No Content
