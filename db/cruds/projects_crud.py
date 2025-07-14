import sqlite3
import uuid
from datetime import datetime, timezone
import logging
from .generic_crud import _manage_conn # get_db_connection is not used directly

logger = logging.getLogger(__name__)

@_manage_conn
def add_project(project_data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Adds a new project to the Projects table.
    Expected project_data keys: client_id, project_name, description,
    start_date, deadline_date, budget, status_id.
    Optional keys: manager_team_member_id, priority.
    """
    logging.info(f"projects_crud.add_project: Attempting to add project with data: {project_data}")
    cursor = conn.cursor()
    new_project_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()

    # Basic validation
    required_fields = ['client_id', 'project_name', 'status_id']
    for field in required_fields:
        if field not in project_data or project_data[field] is None:
            logger.error(f"Field '{field}' is required to add a project.")
            return None

    sql = """
        INSERT INTO Projects (
            project_id, client_id, project_name, description,
            start_date, deadline_date, budget, status_id,
            manager_team_member_id, priority, progress_percentage,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_project_id,
        project_data['client_id'],
        project_data['project_name'],
        project_data.get('description'),
        project_data.get('start_date'), # Should be in ISO format if string, or date object
        project_data.get('deadline_date'), # Same as start_date
        project_data.get('budget'), # Should be REAL/float
        project_data['status_id'], # Should be INTEGER
        project_data.get('manager_team_member_id'), # TEXT (user_id)
        project_data.get('priority', 0), # INTEGER, default 0
        project_data.get('progress_percentage', 0), # INTEGER, default 0
        now_utc,
        now_utc
    )
    try:
        cursor.execute(sql, params)
        logger.info(f"Project '{project_data['project_name']}' added with ID: {new_project_id} for client {project_data['client_id']}.")
        return new_project_id
    except sqlite3.Error as e:
        logger.error(f"projects_crud.add_project: Failed to add project with data {project_data}. Error: {type(e).__name__} - {e}", exc_info=True)
        return None

@_manage_conn
def get_project_by_id(project_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a project by its ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Projects WHERE project_id = ?", (project_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_projects_by_client_id(client_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """Retrieves all projects for a given client_id, ordered by creation date."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Projects WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_project(project_id: str, project_data: dict, conn: sqlite3.Connection = None) -> bool:
    """
    Updates an existing project.
    Valid fields in project_data: project_name, description, start_date,
    deadline_date, budget, status_id, manager_team_member_id, priority, progress_percentage.
    """
    cursor = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()

    valid_fields = [
        'project_name', 'description', 'start_date', 'deadline_date',
        'budget', 'status_id', 'manager_team_member_id', 'priority', 'progress_percentage',
        'client_id' # Allow updating client_id if necessary, though less common.
    ]

    fields_to_update = {k: v for k, v in project_data.items() if k in valid_fields}

    if not fields_to_update:
        logger.info(f"No valid fields provided for updating project {project_id}.")
        # Optionally, still update updated_at if desired, but typically only if other data changes.
        return False

    fields_to_update['updated_at'] = now_utc

    set_clauses = [f"{field} = ?" for field in fields_to_update.keys()]
    params = list(fields_to_update.values())
    params.append(project_id)

    sql = f"UPDATE Projects SET {', '.join(set_clauses)} WHERE project_id = ?"

    try:
        cursor.execute(sql, tuple(params))
        if cursor.rowcount > 0:
            logger.info(f"Project {project_id} updated successfully.")
            return True
        logger.warning(f"No project found with ID {project_id} to update, or data was the same.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error updating project {project_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_project(project_id: str, conn: sqlite3.Connection = None) -> bool:
    """Deletes a project by its ID (hard delete)."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Projects WHERE project_id = ?", (project_id,))
        if cursor.rowcount > 0:
            logger.info(f"Project {project_id} deleted successfully.")
            return True
        logger.warning(f"No project found with ID {project_id} to delete.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error deleting project {project_id}: {e}", exc_info=True)
        return False

@_manage_conn
def get_all_projects(skip: int = 0, limit: int = 100, conn: sqlite3.Connection = None) -> list[dict]:
    """Retrieves all projects with pagination."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Projects ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, skip))
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def get_total_projects_count(conn: sqlite3.Connection = None) -> int:
    """Returns the total number of projects."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Projects")
        count = cursor.fetchone()[0]
        return count if count is not None else 0
    except sqlite3.Error as e:
        logger.error(f"Database error in get_total_projects_count: {e}", exc_info=True)
        return 0

@_manage_conn
def get_active_projects_count(conn: sqlite3.Connection = None) -> int:
    """
    Returns the count of active projects.
    'Active' is defined by not having a status that is marked as 'is_completion_status = TRUE'
    or 'is_archival_status = TRUE' in StatusSettings table.
    This requires a JOIN with StatusSettings.
    """
    cursor = conn.cursor()
    sql = """
        SELECT COUNT(p.project_id)
        FROM Projects p
        LEFT JOIN StatusSettings ss ON p.status_id = ss.status_id
        WHERE (ss.is_completion_status = FALSE OR ss.is_completion_status IS NULL)
          AND (ss.is_archival_status = FALSE OR ss.is_archival_status IS NULL)
    """
    try:
        cursor.execute(sql)
        count = cursor.fetchone()[0]
        return count if count is not None else 0
    except sqlite3.Error as e:
        logger.error(f"Database error in get_active_projects_count: {e}", exc_info=True)
        return 0

@_manage_conn
def get_active_project_count_by_country_id(country_id: int, conn: sqlite3.Connection = None) -> int:
    """
    Counts active projects for clients in a specific country.
    'Active' means project status is not marked as completion or archival.
    """
    cursor = conn.cursor()
    # This query assumes StatusSettings table has is_completion_status and is_archival_status columns
    # and that Clients table has country_id.
    sql = """
        SELECT COUNT(p.project_id) as active_project_count
        FROM Projects p
        JOIN Clients c ON p.client_id = c.client_id
        LEFT JOIN StatusSettings ss ON p.status_id = ss.status_id
        WHERE c.country_id = ?
          AND (c.is_deleted IS NULL OR c.is_deleted = 0)
          AND (p.is_deleted IS NULL OR p.is_deleted = 0)
          AND (ss.is_completion_status = FALSE OR ss.is_completion_status IS NULL)
          AND (ss.is_archival_status = FALSE OR ss.is_archival_status IS NULL)
          AND (ss.status_type = 'Project' OR ss.status_type IS NULL)
    """
    try:
        cursor.execute(sql, (country_id,))
        row = cursor.fetchone()
        return row['active_project_count'] if row else 0
    except sqlite3.Error as e:
        logger.error(f"DB error in get_active_project_count_by_country_id for country_id {country_id}: {e}", exc_info=True)
        return 0
    except Exception as ex:
        logger.error(f"Unexpected error in get_active_project_count_by_country_id for country_id {country_id}: {ex}", exc_info=True)
        return 0

__all__ = [
    "add_project",
    "get_project_by_id",
    "get_projects_by_client_id",
    "update_project",
    "delete_project",
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

@_manage_conn
def get_overdue_tasks_count(conn: sqlite3.Connection = None) -> int:
    """
    Counts the number of overdue tasks.
    A task is considered overdue if its due_date has passed and it is not completed.
    """
    cursor = conn.cursor()
    # Get the current date in YYYY-MM-DD format for comparison
    current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    # SQL to count tasks where due_date is past and completed_at is NULL
    # This assumes due_date is stored in a format comparable to the current_date string.
    sql = """
        SELECT COUNT(task_id)
        FROM Tasks
        WHERE due_date < ? AND (completed_at IS NULL OR completed_at = '')
    """
    try:
        cursor.execute(sql, (current_date,))
        count = cursor.fetchone()[0]
        return count if count is not None else 0
    except sqlite3.Error as e:
        logger.error(f"Database error in get_overdue_tasks_count: {e}", exc_info=True)
        return 0

# Placeholder functions
@_manage_conn
def search_projects(search_term: str, conn: sqlite3.Connection = None) -> list[dict]:
    logger.warning("Placeholder function `search_projects` called. Not yet implemented.")
    return []

@_manage_conn
def get_projects_by_status(status_id: int, conn: sqlite3.Connection = None) -> list[dict]:
    logger.warning("Placeholder function `get_projects_by_status` called. Not yet implemented.")
    return []

@_manage_conn
def get_projects_by_user(user_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    logger.warning("Placeholder function `get_projects_by_user` called. Not yet implemented.")
    return []
