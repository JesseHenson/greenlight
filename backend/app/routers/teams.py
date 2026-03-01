import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.group import Team, TeamMember, TeamRead, GroupRole, PendingTeamInvite
from app.models.user import User
from app.services.clerk_auth import send_clerk_invitation

router = APIRouter(prefix="/api/teams", tags=["teams"])


class CreateTeamRequest(BaseModel):
    name: str = ""


class InviteRequest(BaseModel):
    email: str


@router.post("", response_model=TeamRead)
def create_team(data: CreateTeamRequest, session: SessionDep, current_user: CurrentUser):
    team = Team(name=data.name)
    session.add(team)
    session.commit()
    session.refresh(team)

    member = TeamMember(
        group_id=team.id,
        user_id=current_user.id,
        role=GroupRole.owner,
    )
    session.add(member)
    session.commit()

    return TeamRead(
        id=team.id,
        name=team.name,
        members=[{
            "user_id": current_user.id,
            "user_name": current_user.name,
            "email": current_user.email,
            "role": GroupRole.owner,
        }],
    )


@router.get("", response_model=list[TeamRead])
def list_teams(session: SessionDep, current_user: CurrentUser):
    stmt = (
        select(Team)
        .join(TeamMember, TeamMember.group_id == Team.id)
        .where(TeamMember.user_id == current_user.id)
    )
    teams = session.exec(stmt).all()
    result = []
    for t in teams:
        members = session.exec(
            select(TeamMember).where(TeamMember.group_id == t.id)
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
        result.append(TeamRead(id=t.id, name=t.name, members=member_list))
    return result


@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: int, session: SessionDep, current_user: CurrentUser):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    membership = session.exec(
        select(TeamMember).where(
            TeamMember.group_id == team_id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    members = session.exec(
        select(TeamMember).where(TeamMember.group_id == team_id)
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

    return TeamRead(id=team.id, name=team.name, members=member_list)


@router.get("/{team_id}/pending-invites")
def list_pending_invites(team_id: int, session: SessionDep, current_user: CurrentUser):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    membership = session.exec(
        select(TeamMember).where(
            TeamMember.group_id == team_id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    invites = session.exec(
        select(PendingTeamInvite).where(PendingTeamInvite.group_id == team_id)
    ).all()
    return [{"id": i.id, "email": i.email, "created_at": i.created_at.isoformat()} for i in invites]


@router.delete("/{team_id}/pending-invites/{invite_id}")
def cancel_pending_invite(team_id: int, invite_id: int, session: SessionDep, current_user: CurrentUser):
    membership = session.exec(
        select(TeamMember).where(
            TeamMember.group_id == team_id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    invite = session.get(PendingTeamInvite, invite_id)
    if not invite or invite.group_id != team_id:
        raise HTTPException(status_code=404, detail="Invite not found")

    session.delete(invite)
    session.commit()
    return {"message": "Invite cancelled"}


class UpdateTeamRequest(BaseModel):
    name: str


@router.patch("/{team_id}")
def update_team(team_id: int, data: UpdateTeamRequest, session: SessionDep, current_user: CurrentUser):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    membership = session.exec(
        select(TeamMember).where(
            TeamMember.group_id == team_id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    team.name = data.name
    session.add(team)
    session.commit()
    session.refresh(team)
    return {"message": "Team updated", "name": team.name}


@router.post("/{team_id}/invite")
def invite_to_team(
    team_id: int,
    data: InviteRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    membership = session.exec(
        select(TeamMember).where(
            TeamMember.group_id == team_id,
            TeamMember.user_id == current_user.id,
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    target_user = session.exec(select(User).where(User.email == data.email)).first()

    if target_user:
        existing = session.exec(
            select(TeamMember).where(
                TeamMember.group_id == team_id,
                TeamMember.user_id == target_user.id,
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already a member of this team")

        session.add(TeamMember(
            group_id=team_id,
            user_id=target_user.id,
            role=GroupRole.member,
        ))
        session.commit()
        return {"message": f"Added {target_user.name} to the team", "status": "added"}

    existing_invite = session.exec(
        select(PendingTeamInvite).where(
            PendingTeamInvite.group_id == team_id,
            PendingTeamInvite.email == data.email,
        )
    ).first()
    if existing_invite:
        raise HTTPException(status_code=400, detail="An invitation has already been sent to this email")

    redirect_url = os.environ.get(
        "APP_URL",
        "https://greenlight.app",
    )
    send_clerk_invitation(data.email, redirect_url)

    session.add(PendingTeamInvite(
        group_id=team_id,
        email=data.email,
        invited_by=current_user.id,
    ))
    session.commit()

    return {
        "message": f"Invitation sent to {data.email}. They'll join your team when they sign in.",
        "status": "invited",
    }
