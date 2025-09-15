import sqlite3
import uuid
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from app.models.db.projects.project import Project
from app.models.db.settings.status_setting import StatusSetting
from ..generic_crud import _manage_conn

from app.models.db.clients.client import Client

logger = logging.getLogger(__name__)

def add_project(db: Session, project_data: dict) -> str | None:
    """
    Adds a new project to the Projects table.
    Expected project_data keys: client_id, project_name, description,
    start_date, deadline_date, budget, status_id.
    Optional keys: manager_team_member_id, priority.
    """
    logging.info(f"projects_crud.add_project: Attempting to add project with data: {project_data}")
    new_project_id = str(uuid.uuid4())

    new_project = Project(
        project_id=new_project_id,
        **project_data
    )
    db.add(new_project)
    try:
        db.commit()
        logger.info(f"Project '{project_data['project_name']}' added with ID: {new_project_id} for client {project_data['client_id']}.")
        return new_project_id
    except Exception as e:
        logger.error(f"projects_crud.add_project: Failed to add project with data {project_data}. Error: {type(e).__name__} - {e}", exc_info=True)
        db.rollback()
        return None

def get_project_by_id(db: Session, project_id: str) -> dict | None:
    """Retrieves a project by its ID."""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    return project.__dict__ if project else None

def get_projects_by_client_id(db: Session, client_id: str) -> list[dict]:
    """Retrieves all projects for a given client_id, ordered by creation date."""
    return [p.__dict__ for p in db.query(Project).filter(Project.client_id == client_id).order_by(Project.created_at.desc()).all()]

def get_project_by_client_id(db: Session, client_id: str) -> dict | None:
    """Retrieves the first project for a given client_id."""
    project = db.query(Project).filter(Project.client_id == client_id).first()
    return project.__dict__ if project else None

def update_project(db: Session, project_id: str, project_data: dict) -> bool:
    """
    Updates an existing project.
    Valid fields in project_data: project_name, description, start_date,
    deadline_date, budget, status_id, manager_team_member_id, priority, progress_percentage.
    """
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        return False

    for key, value in project_data.items():
        setattr(project, key, value)

    try:
        db.commit()
        logger.info(f"Project {project_id} updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Database error updating project {project_id}: {e}", exc_info=True)
        db.rollback()
        return False

from app.models.db.misc.tasks import Task

def delete_project_and_tasks(db: Session, project_id: str) -> bool:
    """Deletes all tasks for a project and then deletes the project itself."""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        return False

    try:
        # Delete associated tasks first
        db.query(Task).filter(Task.project_id == project_id).delete(synchronize_session=False)

        # Then delete the project
        db.delete(project)

        db.commit()
        logger.info(f"Project {project_id} and its tasks deleted successfully.")
        return True
    except Exception as e:
        logger.error(f"Database error deleting project {project_id} and its tasks: {e}", exc_info=True)
        db.rollback()
        return False

def delete_project(db: Session, project_id: str) -> bool:
    """Deletes a project by its ID (hard delete)."""
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        return False

    db.delete(project)
    try:
        db.commit()
        logger.info(f"Project {project_id} deleted successfully.")
        return True
    except Exception as e:
        logger.error(f"Database error deleting project {project_id}: {e}", exc_info=True)
        db.rollback()
        return False

def get_all_projects(db: Session, skip: int = 0, limit: int = 100) -> list[dict]:
    """Retrieves all projects with pagination."""
    return [p.__dict__ for p in db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()]

def get_total_projects_count(db: Session) -> int:
    """Returns the total number of projects."""
    try:
        return db.query(Project).count()
    except Exception as e:
        logger.error(f"Database error in get_total_projects_count: {e}", exc_info=True)
        return 0

def get_active_projects_count(db: Session) -> int:
    """
    Returns the count of active projects.
    'Active' is defined by not having a status that is marked as 'is_completion_status = TRUE'
    or 'is_archival_status = TRUE' in StatusSettings table.
    This requires a JOIN with StatusSettings.
    """
    try:
        count = (
            db.query(Project)
            .join(StatusSetting, Project.status_id == StatusSetting.status_id, isouter=True)
            .filter(
                (StatusSetting.is_completion_status == False) | (StatusSetting.is_completion_status == None),
                (StatusSetting.is_archival_status == False) | (StatusSetting.is_archival_status == None),
            )
            .count()
        )
        return count
    except Exception as e:
        logger.error(f"Database error in get_active_projects_count: {e}", exc_info=True)
        return 0

def get_active_project_count_by_country_id(db: Session, country_id: int) -> int:
    """
    Counts active projects for clients in a specific country.
    'Active' means project status is not marked as completion or archival.
    """
    try:
        count = (
            db.query(Project)
            .join(Client, Project.client_id == Client.client_id)
            .join(StatusSetting, Project.status_id == StatusSetting.status_id, isouter=True)
            .filter(Client.country_id == country_id)
            .filter(Client.is_deleted == False)
            .filter(Project.is_deleted == False)
            .filter(
                (StatusSetting.is_completion_status == False) | (StatusSetting.is_completion_status == None),
                (StatusSetting.is_archival_status == False) | (StatusSetting.is_archival_status == None),
                (StatusSetting.status_type == 'Project') | (StatusSetting.status_type == None)
            )
            .count()
        )
        return count
    except Exception as e:
        logger.error(f"DB error in get_active_project_count_by_country_id for country_id {country_id}: {e}", exc_info=True)
        return 0

__all__ = [
    "add_project",
    "get_project_by_id",
    "get_projects_by_client_id",
    "get_project_by_client_id",
    "update_project",
    "delete_project",
    "delete_project_and_tasks",
    "get_all_projects",
    "get_total_projects_count",
    "get_active_projects_count",
    "get_active_project_count_by_country_id", # Added new function
    # Added placeholders
    "search_projects",
    "get_projects_by_status",
    "get_projects_by_user",
    "get_overdue_tasks_count",
]

def get_overdue_tasks_count(db: Session) -> int:
    """
    Counts the number of overdue tasks.
    A task is considered overdue if its due_date has passed and it is not completed.
    """
    from app.models.db.misc.tasks import Task
    current_date = datetime.now(timezone.utc)
    try:
        count = (
            db.query(Task)
            .filter(Task.due_date < current_date, (Task.completed_at == None) | (Task.completed_at == ''))
            .count()
        )
        return count
    except Exception as e:
        logger.error(f"Database error in get_overdue_tasks_count: {e}", exc_info=True)
        return 0

# Placeholder functions
def search_projects(db: Session, search_term: str) -> list[dict]:
    logger.warning("Placeholder function `search_projects` called. Not yet implemented.")
    return []

def get_projects_by_status(db: Session, status_id: int) -> list[dict]:
    logger.warning("Placeholder function `get_projects_by_status` called. Not yet implemented.")
    return []

def get_projects_by_user(db: Session, user_id: str) -> list[dict]:
    logger.warning("Placeholder function `get_projects_by_user` called. Not yet implemented.")
    return []
