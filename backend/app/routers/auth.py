from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.dependencies import CurrentUser
from app.models.user import User, UserRead
from app.services.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser):
    return current_user


class DevLoginRequest(BaseModel):
    email: str


class DevLoginResponse(BaseModel):
    user: UserRead
    token: str


@router.post("/dev-login", response_model=DevLoginResponse)
def dev_login(body: DevLoginRequest, session: Session = Depends(get_session)):
    if settings.production:
        raise HTTPException(status_code=404, detail="Not found")

    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token(user.id)
    return DevLoginResponse(user=UserRead.model_validate(user), token=token)
