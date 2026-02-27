"""Verify Clerk-issued JWTs using JWKS public keys."""

import logging

import httpx
import jwt as pyjwt
from jwt import PyJWKClient

from app.config import settings

logger = logging.getLogger(__name__)

# Cache the JWKS client — it handles key caching internally
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        # Derive the Clerk Frontend API URL from the publishable key
        # pk_test_xxx or pk_live_xxx -> base64 decode the xxx part to get the domain
        import base64

        key_part = settings.clerk_publishable_key.split("_", 2)[-1]
        padded = key_part + "=" * (4 - len(key_part) % 4)
        domain = base64.b64decode(padded).decode().rstrip("$")
        jwks_url = f"https://{domain}/.well-known/jwks.json"
        logger.info("Clerk JWKS URL: %s", jwks_url)
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def verify_clerk_token(token: str) -> dict | None:
    """Verify a Clerk JWT and return the decoded payload, or None on failure."""
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except Exception as e:
        logger.error("Clerk token verification failed: %s", e)
        return None


def send_clerk_invitation(email: str, redirect_url: str) -> dict | None:
    """Send an invitation email via Clerk. Returns invitation data or None on failure."""
    if not settings.clerk_secret_key:
        logger.error("CLERK_SECRET_KEY not configured")
        return None
    try:
        resp = httpx.post(
            "https://api.clerk.com/v1/invitations",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
            json={
                "email_address": email,
                "redirect_url": redirect_url,
            },
        )
        if resp.status_code not in (200, 201):
            logger.error("Clerk invitation API returned %d: %s", resp.status_code, resp.text)
            return None
        return resp.json()
    except Exception as e:
        logger.error("Clerk invitation API call failed: %s", e)
        return None


def get_clerk_user_info(clerk_user_id: str) -> dict | None:
    """Fetch user details from Clerk Backend API."""
    if not settings.clerk_secret_key:
        logger.error("CLERK_SECRET_KEY not configured")
        return None
    try:
        resp = httpx.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
        )
        if resp.status_code != 200:
            logger.error("Clerk API returned %d: %s", resp.status_code, resp.text)
            return None
        data = resp.json()
        email = ""
        if data.get("email_addresses"):
            primary_id = data.get("primary_email_address_id")
            for ea in data["email_addresses"]:
                if ea["id"] == primary_id:
                    email = ea["email_address"]
                    break
            if not email:
                email = data["email_addresses"][0]["email_address"]
        name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        if not name:
            name = email.split("@")[0]
        return {"clerk_id": clerk_user_id, "email": email, "name": name}
    except Exception as e:
        logger.error("Clerk API call failed: %s", e)
        return None
