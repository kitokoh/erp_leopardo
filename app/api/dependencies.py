from fastapi import Depends, HTTPException, status
from typing import Set
from sqlalchemy.orm import Session

from .models import UserInDB
from .auth import get_current_active_user
from app.services.auth.permissions import has_permission
from app.services.auth.roles import check_user_role, ALL_ROLES
from app.db.session_manager import get_db

class RoleRequired:
    def __init__(self, allowed_roles: Set[str]):
        if not allowed_roles.issubset(ALL_ROLES):
            raise ValueError(f"Invalid role(s) in allowed_roles {allowed_roles - ALL_ROLES}. Must be a subset of {ALL_ROLES}")
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: UserInDB = Depends(get_current_active_user)):
        if not check_user_role(current_user.role, self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized. Allowed roles: {self.allowed_roles}"
            )
        return current_user

class PermissionRequired:
    def __init__(self, permission_identifier: str):
        self.permission_identifier = permission_identifier

    async def __call__(self, conn: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_active_user)):
        if not has_permission(conn, current_user.role, self.permission_identifier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' lacks the required permission: '{self.permission_identifier}'"
            )
        return current_user
