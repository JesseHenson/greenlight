import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.database import get_session
from app.models.user import User
from app.models.group import PendingTeamInvite, TeamMember, GroupRole
from app.services.clerk_auth import verify_clerk_token, get_clerk_user_info

logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    token = credentials.credentials
    payload = verify_clerk_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no subject",
        )

    # Look up existing user by clerk_id
    user = session.exec(select(User).where(User.clerk_id == clerk_id)).first()
    if user:
        _fulfill_pending_invites(session, user)
        return user

    # Auto-provision: fetch user info from Clerk and create local record
    clerk_info = get_clerk_user_info(clerk_id)
    if not clerk_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user information",
        )

    # Check if a user with this email already exists (e.g. from seed data)
    user = session.exec(
        select(User).where(User.email == clerk_info["email"])
    ).first()
    if user:
        # Link existing user to their Clerk ID
        user.clerk_id = clerk_id
        user.name = clerk_info["name"]
        session.add(user)
        session.commit()
        session.refresh(user)
        _fulfill_pending_invites(session, user)
        return user

    # Create brand new user
    user = User(
        clerk_id=clerk_id,
        name=clerk_info["name"],
        email=clerk_info["email"],
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Fulfill any pending team invites for this email
    _fulfill_pending_invites(session, user)

    return user


def _fulfill_pending_invites(session: Session, user: User):
    """Auto-join teams where this user's email was invited."""
    pending = session.exec(
        select(PendingTeamInvite).where(PendingTeamInvite.email == user.email)
    ).all()
    for invite in pending:
        # Check not already a member
        existing = session.exec(
            select(TeamMember).where(
                TeamMember.group_id == invite.group_id,
                TeamMember.user_id == user.id,
            )
        ).first()
        if not existing:
            session.add(TeamMember(
                group_id=invite.group_id,
                user_id=user.id,
                role=GroupRole.member,
            ))
        session.delete(invite)
    if pending:
        session.commit()
        logger.info("Fulfilled %d pending team invite(s) for %s", len(pending), user.email)


CurrentUser = Annotated[User, Depends(get_current_user)]
