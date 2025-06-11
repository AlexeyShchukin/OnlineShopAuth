from typing import Annotated

from fastapi import Depends, APIRouter

from src.api.dependencies.user_dependency import get_current_user
from src.api.schemas.user import UserPublic

user_router = APIRouter(
    prefix="/api/v1",
    tags=["Users"]
)


@user_router.get("/users/profile/", response_model=UserPublic)
async def read_user(current_user: Annotated[UserPublic, Depends(get_current_user)]) -> UserPublic:
    return current_user


