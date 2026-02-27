from fastapi import APIRouter

from app.dependencies import CurrentUser
from app.models.user import UserRead

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser):
    return current_user
