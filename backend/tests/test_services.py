"""Tests for auth and clerk_auth services."""

from unittest.mock import patch, MagicMock

from app.services.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("my-secret")
    assert verify_password("my-secret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_decode_invalid_token():
    assert decode_access_token("garbage.token.here") is None


def test_clerk_verify_token_failure():
    from app.services.clerk_auth import verify_clerk_token
    # An invalid token should return None
    with patch("app.services.clerk_auth._get_jwks_client") as mock_jwks:
        mock_jwks.return_value.get_signing_key_from_jwt.side_effect = Exception("bad key")
        result = verify_clerk_token("fake-token")
    assert result is None


def test_clerk_send_invitation_no_key():
    with patch("app.services.clerk_auth.settings") as mock_settings:
        mock_settings.clerk_secret_key = ""
        from app.services.clerk_auth import send_clerk_invitation
        result = send_clerk_invitation("test@test.com", "http://localhost")
    assert result is None


def test_clerk_send_invitation_api_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.text = "Unprocessable"

    with patch("app.services.clerk_auth.settings") as mock_settings, \
         patch("app.services.clerk_auth.httpx.post", return_value=mock_resp):
        mock_settings.clerk_secret_key = "sk_test_fake"
        from app.services.clerk_auth import send_clerk_invitation
        result = send_clerk_invitation("test@test.com", "http://localhost")
    assert result is None


def test_clerk_send_invitation_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "inv_123"}

    with patch("app.services.clerk_auth.settings") as mock_settings, \
         patch("app.services.clerk_auth.httpx.post", return_value=mock_resp):
        mock_settings.clerk_secret_key = "sk_test_fake"
        from app.services.clerk_auth import send_clerk_invitation
        result = send_clerk_invitation("test@test.com", "http://localhost")
    assert result == {"id": "inv_123"}


def test_clerk_get_user_info_no_key():
    with patch("app.services.clerk_auth.settings") as mock_settings:
        mock_settings.clerk_secret_key = ""
        from app.services.clerk_auth import get_clerk_user_info
        result = get_clerk_user_info("user_123")
    assert result is None


def test_clerk_get_user_info_api_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not found"

    with patch("app.services.clerk_auth.settings") as mock_settings, \
         patch("app.services.clerk_auth.httpx.get", return_value=mock_resp):
        mock_settings.clerk_secret_key = "sk_test_fake"
        from app.services.clerk_auth import get_clerk_user_info
        result = get_clerk_user_info("user_123")
    assert result is None


def test_clerk_get_user_info_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "first_name": "Jane",
        "last_name": "Doe",
        "primary_email_address_id": "ea_1",
        "email_addresses": [
            {"id": "ea_1", "email_address": "jane@test.com"},
        ],
    }

    with patch("app.services.clerk_auth.settings") as mock_settings, \
         patch("app.services.clerk_auth.httpx.get", return_value=mock_resp):
        mock_settings.clerk_secret_key = "sk_test_fake"
        from app.services.clerk_auth import get_clerk_user_info
        result = get_clerk_user_info("user_123")

    assert result["name"] == "Jane Doe"
    assert result["email"] == "jane@test.com"
    assert result["clerk_id"] == "user_123"


def test_clerk_get_user_info_no_name():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "first_name": "",
        "last_name": "",
        "primary_email_address_id": "ea_1",
        "email_addresses": [
            {"id": "ea_1", "email_address": "noname@test.com"},
        ],
    }

    with patch("app.services.clerk_auth.settings") as mock_settings, \
         patch("app.services.clerk_auth.httpx.get", return_value=mock_resp):
        mock_settings.clerk_secret_key = "sk_test_fake"
        from app.services.clerk_auth import get_clerk_user_info
        result = get_clerk_user_info("user_123")

    assert result["name"] == "noname"


def test_clerk_get_user_info_fallback_email():
    """When primary_email_address_id doesn't match, use first email."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "first_name": "Bob",
        "last_name": "",
        "primary_email_address_id": "ea_missing",
        "email_addresses": [
            {"id": "ea_1", "email_address": "fallback@test.com"},
        ],
    }

    with patch("app.services.clerk_auth.settings") as mock_settings, \
         patch("app.services.clerk_auth.httpx.get", return_value=mock_resp):
        mock_settings.clerk_secret_key = "sk_test_fake"
        from app.services.clerk_auth import get_clerk_user_info
        result = get_clerk_user_info("user_123")

    assert result["email"] == "fallback@test.com"
