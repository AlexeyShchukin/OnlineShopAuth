from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException, status

from src.api.dependencies.kafka_dependency import get_event_publisher
from src.api.dependencies.user_dependency import get_current_user, get_user_service
from src.api.schemas.user import UserPublic, UserUpdate
from src.core.security import oauth2_scheme
from src.db.models import User
from src.exceptions.service_exceptions import UserAlreadyExistsException
from src.infrastructure.kafka.event_publisher import EventPublisher
from src.services.user_service import UserService

user_router = APIRouter(tags=["User"])


@user_router.get("/profile", response_model=UserPublic)
async def read_user(
        current_user: Annotated[User, Depends(get_current_user)]
) -> UserPublic:
    return UserPublic.model_validate(current_user)


@user_router.patch("/profile", response_model=UserPublic)
async def update_user(
        user_update: UserUpdate,
        user_service: Annotated[UserService, Depends(get_user_service)],
        token: Annotated[str, Depends(oauth2_scheme)],
        event_publisher: EventPublisher = Depends(get_event_publisher)
) -> UserPublic:
    try:
        updated_user = await user_service.update_user(user_update, token)
    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    await event_publisher.publish_profile_updated(updated_user)

    return UserPublic.model_validate(updated_user)
