"""Authentication service – registration, login, token management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.user import RefreshToken, User, UserRole
from app.models.user_profile import UserProfile
from app.security.password import hash_password, verify_password
from app.security.tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.utils.exceptions import (
    BadRequestError,
    DuplicateResourceError,
    UnauthorizedError,
)


def register_user(
    db: Session,
    username: str,
    password: str,
    email: str | None = None,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a new user with hashed password and empty profile."""
    # Check for duplicate username
    if db.query(User).filter(User.username == username).first():
        raise DuplicateResourceError("Username already taken.")
    # Check for duplicate email
    if email:
        if db.query(User).filter(User.email == email).first():
            raise DuplicateResourceError("Email already registered.")

    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()

    # Create empty profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    """Verify credentials and return the user, or raise 401."""
    user = (
        db.query(User)
        .filter(User.username == username, User.is_active == True, User.is_deleted == False)  # noqa: E712
        .first()
    )
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Invalid username or password.")
    return user


def issue_tokens(db: Session, user: User) -> dict:
    """Create access + refresh tokens, persist refresh hash."""
    access = create_access_token(subject=str(user.id), role=user.role.value)
    raw_refresh, token_hash, expires_at = create_refresh_token(subject=str(user.id))

    rt = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(rt)
    db.commit()

    return {
        "access_token": access,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, raw_refresh: str) -> dict:
    """Validate a refresh token and return a new token pair."""
    payload = decode_token(raw_refresh)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token.")

    token_hash_val = hash_token(raw_refresh)
    rt = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash_val,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
        .first()
    )
    if not rt:
        raise UnauthorizedError("Refresh token not found or revoked.")
    if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise UnauthorizedError("Refresh token expired.")

    user = db.query(User).filter(User.id == rt.user_id, User.is_active == True, User.is_deleted == False).first()  # noqa: E712
    if not user:
        raise UnauthorizedError("User not found or inactive.")

    # Revoke old refresh token
    rt.is_revoked = True
    db.flush()

    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, raw_refresh: str) -> None:
    """Revoke a refresh token (logout)."""
    token_hash_val = hash_token(raw_refresh)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash_val).first()
    if rt:
        rt.is_revoked = True
        db.commit()


def revoke_all_user_tokens(db: Session, user_id: uuid.UUID) -> None:
    """Revoke every refresh token for the user."""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,  # noqa: E712
    ).update({"is_revoked": True})
    db.commit()
