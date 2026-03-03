"""Tests for the email service with mocked Resend API."""

from unittest.mock import patch, MagicMock

from app.services.email import (
    send_email,
    send_waitlist_notification,
    send_team_invite_email,
    send_analysis_complete_email,
)


def test_send_email_no_api_key():
    with patch("app.services.email.settings") as mock_settings:
        mock_settings.resend_api_key = ""
        result = send_email("test@test.com", "Subject", "<h1>Hi</h1>", "Hi")
    assert result is False


def test_send_email_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.httpx.post", return_value=mock_resp):
        mock_settings.resend_api_key = "re_test"
        result = send_email("test@test.com", "Subject", "<h1>Hi</h1>", "Hi")
    assert result is True


def test_send_email_api_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.text = "Invalid"

    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.httpx.post", return_value=mock_resp):
        mock_settings.resend_api_key = "re_test"
        result = send_email("test@test.com", "Subject", "<h1>Hi</h1>", "Hi")
    assert result is False


def test_send_email_exception():
    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.httpx.post", side_effect=Exception("Network error")):
        mock_settings.resend_api_key = "re_test"
        result = send_email("test@test.com", "Subject", "<h1>Hi</h1>", "Hi")
    assert result is False


def test_send_email_list_recipients():
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.httpx.post", return_value=mock_resp) as mock_post:
        mock_settings.resend_api_key = "re_test"
        send_email(["a@test.com", "b@test.com"], "Subject", "<h1>Hi</h1>", "Hi")
    # Verify the list was passed through
    call_json = mock_post.call_args.kwargs["json"]
    assert call_json["to"] == ["a@test.com", "b@test.com"]


def test_send_waitlist_notification():
    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.send_email") as mock_send:
        mock_settings.notify_email = "admin@test.com"
        send_waitlist_notification("Test User", "test@test.com", "March 2, 2026")
    mock_send.assert_called_once()
    args = mock_send.call_args
    assert "admin@test.com" in args[0]
    assert "Test User" in args[0][1]


def test_send_waitlist_notification_no_notify_email():
    with patch("app.services.email.settings") as mock_settings, \
         patch("app.services.email.send_email") as mock_send:
        mock_settings.notify_email = ""
        send_waitlist_notification("Test", "t@t.com", "now")
    mock_send.assert_not_called()


def test_send_team_invite_email():
    with patch("app.services.email.send_email") as mock_send:
        send_team_invite_email("new@test.com", "Alice", "Family Team", "http://localhost")
    mock_send.assert_called_once()
    args = mock_send.call_args[0]
    assert args[0] == "new@test.com"
    assert "Alice" in args[1]


def test_send_analysis_complete_email():
    with patch("app.services.email.send_email") as mock_send:
        send_analysis_complete_email("user@test.com", "Bob", "Bedtime Routine", "http://localhost", 42)
    mock_send.assert_called_once()
    args = mock_send.call_args[0]
    assert args[0] == "user@test.com"
    assert "Bedtime Routine" in args[1]
    assert "/challenges/42/analysis" in args[2]  # html contains the link
