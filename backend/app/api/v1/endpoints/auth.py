"""Authentication endpoints – registration, login, refresh, logout."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user with unique username and optional email."""
    user = auth_service.register_user(
        db=db,
        username=payload.username,
        password=payload.password,
        email=payload.email,
    )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="OAuth2-compatible login returning JWT tokens",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticate with username and password, returns access and refresh tokens."""
    user = auth_service.authenticate_user(
        db=db, username=form_data.username, password=form_data.password
    )
    return auth_service.issue_tokens(db, user)


@router.post(
    "/login/json",
    response_model=TokenResponse,
    summary="JSON-based login endpoint for mobile Flutter client",
)
def login_json(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Alternative JSON-body login endpoint convenient for Flutter REST requests."""
    user = auth_service.authenticate_user(
        db=db, username=payload.username, password=payload.password
    )
    return auth_service.issue_tokens(db, user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue a fresh access token",
)
def refresh_token(
    payload: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Exchange a valid refresh token for a new token pair."""
    return auth_service.refresh_access_token(db, payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out and revoke refresh token",
)
def logout(
    payload: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Revoke the given refresh token."""
    auth_service.revoke_refresh_token(db, payload.refresh_token)
    return MessageResponse(message="Successfully logged out.")
