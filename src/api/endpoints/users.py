from typing import Annotated

from fastapi import Depends, APIRouter

from src.api.dependencies.user_dependency import get_current_user, get_user_service
from src.api.schemas.user import UserPublic, UserUpdate
from src.core.security import oauth2_scheme
from src.services.user_service import UserService

user_router = APIRouter(
    prefix="/api/v1",
    tags=["Users"]
)


@user_router.get("/users/profile/", response_model=UserPublic)
async def read_user(current_user: Annotated[UserPublic, Depends(get_current_user)]) -> UserPublic:
    return current_user


@user_router.patch("/users/profile/", response_model=UserPublic)
async def update_user(
        user_update: UserUpdate,
        user_service: Annotated[UserService, Depends(get_user_service)],
        token: Annotated[str, Depends(oauth2_scheme)]
) -> UserPublic:
    updated_user = await user_service.update_user(user_update, token)
    return updated_user


@user_router.delete("/users/profile/")
async def delete_user(current_user: Annotated[UserPublic, Depends(get_current_user)]) :
    ...
