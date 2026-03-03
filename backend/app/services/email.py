"""Transactional email service via Resend."""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

FROM_ADDRESS = "Greenlight <notifications@propelai.solutions>"


def send_email(to: str | list[str], subject: str, html: str, text: str) -> bool:
    """Send an email via Resend. Returns True on success."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — skipping email")
        return False
    recipients = [to] if isinstance(to, str) else to
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": FROM_ADDRESS,
                "to": recipients,
                "subject": subject,
                "html": html,
                "text": text,
            },
        )
        if resp.status_code != 200:
            logger.error("Resend API returned %d: %s", resp.status_code, resp.text)
            return False
        return True
    except Exception as e:
        logger.error("Resend API call failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Email templates
# ---------------------------------------------------------------------------

_HEADER = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:40px 0;">
<tr><td align="center">
<table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
<tr><td style="background:#059669;padding:24px 32px;">
  <span style="color:#ffffff;font-size:20px;font-weight:700;">Greenlight</span>
</td></tr>"""

_FOOTER = """\
<tr><td style="padding:16px 32px;border-top:1px solid #e5e7eb;">
  <p style="margin:0;color:#9ca3af;font-size:12px;">This is an automated notification from Greenlight.</p>
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def _wrap(body_html: str) -> str:
    return f"{_HEADER}{body_html}{_FOOTER}"


# --- Waitlist signup notification (to founder) ---

def send_waitlist_notification(name: str, email: str, created_at_str: str):
    """Notify the founder about a new waitlist signup."""
    if not settings.notify_email:
        return
    html = _wrap(f"""\
<tr><td style="padding:32px;">
  <h1 style="margin:0 0 8px;font-size:22px;color:#111827;">New Waitlist Signup</h1>
  <p style="margin:0 0 24px;color:#6b7280;font-size:14px;">Someone just joined the Greenlight waitlist.</p>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border-radius:8px;">
    <tr><td style="padding:8px 20px;">
      <span style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;">Name</span><br/>
      <span style="color:#111827;font-size:16px;font-weight:600;">{name}</span>
    </td></tr>
    <tr><td style="padding:8px 20px;">
      <span style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;">Email</span><br/>
      <a href="mailto:{email}" style="color:#059669;font-size:16px;font-weight:600;text-decoration:none;">{email}</a>
    </td></tr>
    <tr><td style="padding:8px 20px;">
      <span style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;">Signed up</span><br/>
      <span style="color:#111827;font-size:14px;">{created_at_str}</span>
    </td></tr>
  </table>
</td></tr>""")
    text = f"New waitlist signup!\n\nName: {name}\nEmail: {email}\nSigned up: {created_at_str}"
    send_email(settings.notify_email, f"New waitlist signup: {name}", html, text)


# --- Team invite email (to invitee) ---

def send_team_invite_email(
    to_email: str,
    inviter_name: str,
    team_name: str,
    app_url: str,
):
    """Send a team invitation email to a new user."""
    html = _wrap(f"""\
<tr><td style="padding:32px;">
  <h1 style="margin:0 0 8px;font-size:22px;color:#111827;">You're Invited!</h1>
  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">
    <strong>{inviter_name}</strong> invited you to join the team
    <strong>{team_name or "their team"}</strong> on Greenlight.
  </p>
  <p style="margin:0 0 24px;color:#6b7280;font-size:14px;">
    Greenlight helps teams brainstorm ideas and get AI-powered analysis —
    so everyone's voice is heard.
  </p>
  <table cellpadding="0" cellspacing="0">
    <tr><td style="background:#059669;border-radius:8px;padding:12px 28px;">
      <a href="{app_url}" style="color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">
        Join the team
      </a>
    </td></tr>
  </table>
</td></tr>""")
    text = (
        f"{inviter_name} invited you to join {team_name or 'their team'} on Greenlight.\n\n"
        f"Sign up here: {app_url}"
    )
    send_email(to_email, f"{inviter_name} invited you to Greenlight", html, text)


# --- Analysis complete email (to all collaborators) ---

def send_analysis_complete_email(
    to_email: str,
    user_name: str,
    challenge_title: str,
    app_url: str,
    challenge_id: int,
):
    """Notify a collaborator that AI analysis is complete."""
    analysis_url = f"{app_url}/challenges/{challenge_id}/analysis"
    html = _wrap(f"""\
<tr><td style="padding:32px;">
  <h1 style="margin:0 0 8px;font-size:22px;color:#111827;">Analysis Complete!</h1>
  <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">Hi {user_name},</p>
  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">
    The AI analysis for <strong>{challenge_title}</strong> is ready.
    Every idea has been evaluated for pros &amp; cons, feasibility, and impact.
  </p>
  <table cellpadding="0" cellspacing="0">
    <tr><td style="background:#059669;border-radius:8px;padding:12px 28px;">
      <a href="{analysis_url}" style="color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">
        View Analysis
      </a>
    </td></tr>
  </table>
</td></tr>""")
    text = (
        f"Hi {user_name},\n\n"
        f"AI analysis for \"{challenge_title}\" is complete.\n\n"
        f"View it here: {analysis_url}"
    )
    send_email(to_email, f"Analysis ready: {challenge_title}", html, text)
