"""User management service."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.audit_log import AuditLog
from app.services.auth_service import revoke_all_user_tokens
from app.utils.exceptions import DuplicateResourceError, ResourceNotFoundError


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise ResourceNotFoundError("User not found.")
    return user


def update_user(db: Session, user: User, update_data: dict) -> User:
    if "username" in update_data and update_data["username"] is not None:
        existing = db.query(User).filter(
            User.username == update_data["username"], User.id != user.id
        ).first()
        if existing:
            raise DuplicateResourceError("Username already taken.")
        user.username = update_data["username"]
    if "email" in update_data and update_data["email"] is not None:
        existing = db.query(User).filter(
            User.email == update_data["email"], User.id != user.id
        ).first()
        if existing:
            raise DuplicateResourceError("Email already registered.")
        user.email = update_data["email"]
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User, actor_id: uuid.UUID | None = None) -> None:
    """Soft-delete user and revoke tokens."""
    user.is_active = False
    user.is_deleted = True
    revoke_all_user_tokens(db, user.id)

    audit = AuditLog(
        actor_id=actor_id or user.id,
        action="user_deleted",
        resource_type="user",
        resource_id=str(user.id),
    )
    db.add(audit)
    db.commit()


def get_profile(db: Session, user_id: uuid.UUID) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        # Create one if missing
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, user_id: uuid.UUID, update_data: dict) -> UserProfile:
    profile = get_profile(db, user_id)
    for key, value in update_data.items():
        if value is not None and hasattr(profile, key):
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
