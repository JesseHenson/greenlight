from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.models.waitlist import WaitlistEntry, WaitlistCreate, WaitlistRead

router = APIRouter(prefix="/api/waitlist", tags=["waitlist"])


@router.post("", response_model=WaitlistRead)
def join_waitlist(data: WaitlistCreate, session: SessionDep):
    existing = session.exec(
        select(WaitlistEntry).where(WaitlistEntry.email == data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You're already on the waitlist!")

    entry = WaitlistEntry(name=data.name, email=data.email)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("", response_model=list[WaitlistRead])
def list_waitlist(session: SessionDep):
    entries = session.exec(
        select(WaitlistEntry).order_by(WaitlistEntry.created_at.desc())  # type: ignore
    ).all()
    return entries


@router.get("/count")
def waitlist_count(session: SessionDep):
    entries = session.exec(select(WaitlistEntry)).all()
    return {"count": len(entries)}


@router.delete("/{entry_id}")
def remove_from_waitlist(entry_id: int, session: SessionDep):
    entry = session.get(WaitlistEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    session.delete(entry)
    session.commit()
    return {"message": "Removed from waitlist"}
