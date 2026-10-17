"""Permission helpers for role-based access control."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.models.user import UserRole


def require_admin(role: str) -> None:
    """Raise 403 if the role is not ADMIN."""
    if role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required.",
        )


def require_owner_or_admin(resource_owner_id: str, current_user_id: str, role: str) -> None:
    """Raise 403 unless the caller owns the resource or is an admin."""
    if str(resource_owner_id) != str(current_user_id) and role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
