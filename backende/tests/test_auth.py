"""Tests for authentication and token lifecycle."""

import pytest
from fastapi import status


def test_register_user_success(client):
    """Test standard user registration."""
    payload = {
        "username": "elderly_user_1",
        "password": "SecurePassword123!",
        "email": "elderly1@example.com",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["username"] == "elderly_user_1"
    assert data["email"] == "elderly1@example.com"
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_username_fails(client):
    """Test duplicate usernames are rejected."""
    payload = {
        "username": "duplicate_user",
        "password": "SecurePassword123!",
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_409_CONFLICT


def test_login_success(client, test_user):
    """Test successful OAuth2 login returns tokens."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.username, "password": "Password123!"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_json_success(client, test_user):
    """Test JSON-based login for mobile apps."""
    resp = client.post(
        "/api/v1/auth/login/json",
        json={"username": test_user.username, "password": "Password123!"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "access_token" in resp.json()


def test_login_incorrect_password_fails(client, test_user):
    """Test login failure with wrong password."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.username, "password": "WrongPassword!"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert "access_token" not in resp.json()


def test_refresh_token_rotation(client, test_user):
    """Test refreshing token generates a new pair and revokes old token."""
    login_resp = client.post(
        "/api/v1/auth/login/json",
        json={"username": test_user.username, "password": "Password123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    ref_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_resp.status_code == status.HTTP_200_OK
    new_data = ref_resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data

    # Old refresh token should now be revoked and rejected
    reused_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reused_resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_revokes_token(client, test_user):
    """Test logout revokes the refresh token."""
    login_resp = client.post(
        "/api/v1/auth/login/json",
        json={"username": test_user.username, "password": "Password123!"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == status.HTTP_200_OK

    ref_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_resp.status_code == status.HTTP_401_UNAUTHORIZED
