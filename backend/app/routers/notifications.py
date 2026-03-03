from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.dependencies import CurrentUser
from app.models.notification import Notification, NotificationRead

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(session: SessionDep, current_user: CurrentUser):
    notifications = session.exec(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())  # type: ignore
        .limit(50)
    ).all()
    return notifications


@router.get("/unread-count")
def unread_count(session: SessionDep, current_user: CurrentUser):
    notifications = session.exec(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.read == False,  # noqa: E712
        )
    ).all()
    return {"count": len(notifications)}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, session: SessionDep, current_user: CurrentUser):
    notif = session.get(Notification, notification_id)
    if not notif or notif.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    session.add(notif)
    session.commit()
    return {"message": "Marked as read"}


@router.post("/read-all")
def mark_all_read(session: SessionDep, current_user: CurrentUser):
    notifications = session.exec(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.read == False,  # noqa: E712
        )
    ).all()
    for n in notifications:
        n.read = True
        session.add(n)
    session.commit()
    return {"message": f"Marked {len(notifications)} as read"}
