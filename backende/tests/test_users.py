"""Tests for user accounts, profiles, unauthenticated access, and deletion."""

from fastapi import status


def test_unauthenticated_access_rejected(client):
    """Test accessing protected endpoints without token returns 401."""
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    resp2 = client.get("/api/v1/profiles/me")
    assert resp2.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_me(client, user_auth_headers, test_user):
    """Test fetching own profile with valid auth token."""
    resp = client.get("/api/v1/users/me", headers=user_auth_headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["id"] == str(test_user.id)
    assert data["username"] == test_user.username


def test_update_user_me(client, user_auth_headers):
    """Test updating user account details."""
    resp = client.patch(
        "/api/v1/users/me",
        headers=user_auth_headers,
        json={"email": "new_email@example.com"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["email"] == "new_email@example.com"


def test_profile_read_and_update(client, user_auth_headers):
    """Test profile preferences (age, language, region)."""
    # Read default profile
    resp = client.get("/api/v1/profiles/me", headers=user_auth_headers)
    assert resp.status_code == status.HTTP_200_OK

    # Update profile for an elderly user in Assam (NER India)
    update_data = {
        "display_name": "Grandpa Ankur",
        "age": 74,
        "gender": "male",
        "preferred_language": "as",  # Assamese
        "region": "Assam, NER",
    }
    resp = client.patch("/api/v1/profiles/me", headers=user_auth_headers, json=update_data)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["display_name"] == "Grandpa Ankur"
    assert data["age"] == 74
    assert data["preferred_language"] == "as"
    assert data["region"] == "Assam, NER"


def test_account_deletion_soft_delete(client, user_auth_headers, test_user):
    """Test user account deletion deactivates account and revokes access."""
    del_resp = client.delete("/api/v1/users/me", headers=user_auth_headers)
    assert del_resp.status_code == status.HTTP_200_OK

    # Access with the same token should now be rejected as account is inactive
    me_resp = client.get("/api/v1/users/me", headers=user_auth_headers)
    assert me_resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_metrics_access(client, admin_auth_headers, user_auth_headers):
    """Test admin endpoints require admin role."""
    # Regular user denied
    user_resp = client.get("/api/v1/admin/metrics", headers=user_auth_headers)
    assert user_resp.status_code == status.HTTP_403_FORBIDDEN

    # Admin granted
    admin_resp = client.get("/api/v1/admin/metrics", headers=admin_auth_headers)
    assert admin_resp.status_code == status.HTTP_200_OK
    assert "total_registered_users" in admin_resp.json()
