import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.group import ParentGroup, ParentGroupMember, ParentGroupRead, GroupRole, PendingGroupInvite
from app.models.user import User
from app.services.clerk_auth import send_clerk_invitation

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    name: str = ""


class InviteRequest(BaseModel):
    email: str


@router.post("", response_model=ParentGroupRead)
def create_group(data: CreateGroupRequest, session: SessionDep, current_user: CurrentUser):
    group = ParentGroup(name=data.name)
    session.add(group)
    session.commit()
    session.refresh(group)

    # Add creator as owner
    member = ParentGroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role=GroupRole.owner,
    )
    session.add(member)
    session.commit()

    return ParentGroupRead(
        id=group.id,
        name=group.name,
        members=[{
            "user_id": current_user.id,
            "user_name": current_user.name,
            "email": current_user.email,
            "role": GroupRole.owner,
        }],
    )


@router.get("", response_model=list[ParentGroupRead])
def list_groups(session: SessionDep, current_user: CurrentUser):
    # Get groups the current user belongs to
    stmt = (
        select(ParentGroup)
        .join(ParentGroupMember, ParentGroupMember.group_id == ParentGroup.id)
        .where(ParentGroupMember.user_id == current_user.id)
    )
    groups = session.exec(stmt).all()
    result = []
    for g in groups:
        members = session.exec(
            select(ParentGroupMember).where(ParentGroupMember.group_id == g.id)
        ).all()
        member_list = []
        for m in members:
            u = session.get(User, m.user_id)
            member_list.append({
                "user_id": m.user_id,
                "user_name": u.name if u else "Unknown",
                "email": u.email if u else "",
                "role": m.role,
            })
        result.append(ParentGroupRead(id=g.id, name=g.name, members=member_list))
    return result


@router.get("/{group_id}", response_model=ParentGroupRead)
def get_group(group_id: int, session: SessionDep, current_user: CurrentUser):
    group = session.get(ParentGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify user is a member
    membership = session.exec(
        select(ParentGroupMember).where(
            ParentGroupMember.group_id == group_id,
            ParentGroupMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    members = session.exec(
        select(ParentGroupMember).where(ParentGroupMember.group_id == group_id)
    ).all()
    member_list = []
    for m in members:
        u = session.get(User, m.user_id)
        member_list.append({
            "user_id": m.user_id,
            "user_name": u.name if u else "Unknown",
            "email": u.email if u else "",
            "role": m.role,
        })

    return ParentGroupRead(id=group.id, name=group.name, members=member_list)


@router.get("/{group_id}/pending-invites")
def list_pending_invites(group_id: int, session: SessionDep, current_user: CurrentUser):
    group = session.get(ParentGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = session.exec(
        select(ParentGroupMember).where(
            ParentGroupMember.group_id == group_id,
            ParentGroupMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    invites = session.exec(
        select(PendingGroupInvite).where(PendingGroupInvite.group_id == group_id)
    ).all()
    return [{"id": i.id, "email": i.email, "created_at": i.created_at.isoformat()} for i in invites]


@router.delete("/{group_id}/pending-invites/{invite_id}")
def cancel_pending_invite(group_id: int, invite_id: int, session: SessionDep, current_user: CurrentUser):
    membership = session.exec(
        select(ParentGroupMember).where(
            ParentGroupMember.group_id == group_id,
            ParentGroupMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    invite = session.get(PendingGroupInvite, invite_id)
    if not invite or invite.group_id != group_id:
        raise HTTPException(status_code=404, detail="Invite not found")

    session.delete(invite)
    session.commit()
    return {"message": "Invite cancelled"}


class UpdateGroupRequest(BaseModel):
    name: str


@router.patch("/{group_id}")
def update_group(group_id: int, data: UpdateGroupRequest, session: SessionDep, current_user: CurrentUser):
    group = session.get(ParentGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = session.exec(
        select(ParentGroupMember).where(
            ParentGroupMember.group_id == group_id,
            ParentGroupMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    group.name = data.name
    session.add(group)
    session.commit()
    session.refresh(group)
    return {"message": "Group updated", "name": group.name}


@router.post("/{group_id}/invite")
def invite_to_group(
    group_id: int,
    data: InviteRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    group = session.get(ParentGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify current user is a member
    membership = session.exec(
        select(ParentGroupMember).where(
            ParentGroupMember.group_id == group_id,
            ParentGroupMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    # Find target user by email
    target_user = session.exec(select(User).where(User.email == data.email)).first()

    if target_user:
        # User exists — add them directly
        existing = session.exec(
            select(ParentGroupMember).where(
                ParentGroupMember.group_id == group_id,
                ParentGroupMember.user_id == target_user.id,
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already a member of this group")

        session.add(ParentGroupMember(
            group_id=group_id,
            user_id=target_user.id,
            role=GroupRole.member,
        ))
        session.commit()
        return {"message": f"Added {target_user.name} to the group", "status": "added"}

    # User not in our DB — check if already invited
    existing_invite = session.exec(
        select(PendingGroupInvite).where(
            PendingGroupInvite.group_id == group_id,
            PendingGroupInvite.email == data.email,
        )
    ).first()
    if existing_invite:
        raise HTTPException(status_code=400, detail="An invitation has already been sent to this email")

    # Try sending a Clerk invitation email
    redirect_url = os.environ.get(
        "APP_URL",
        "https://coparent-138789694812.us-central1.run.app",
    )
    send_clerk_invitation(data.email, redirect_url)
    # Even if Clerk invitation fails (e.g. user already has Clerk account),
    # store the pending invite so they auto-join on next sign-in

    session.add(PendingGroupInvite(
        group_id=group_id,
        email=data.email,
        invited_by=current_user.id,
    ))
    session.commit()

    return {
        "message": f"Invitation sent to {data.email}. They'll join your group when they sign in.",
        "status": "invited",
    }
