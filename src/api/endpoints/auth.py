import secrets
from typing import Annotated, Any
from uuid import UUID

import aiohttp
from redis.asyncio import Redis
from fastapi import Depends, APIRouter, Request, status, Response, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse

from src.api.dependencies.oauth_dependency import get_oauth_service
from src.api.schemas.oauth import OAuthResponse
from src.exceptions.service_exceptions import (
    TokenAlreadyUsedException,
    TokenNotFoundException,
    UserNotFoundException,
    InvalidTokenException,
    MissingTokenException,
)
from src.loggers.loggers import logger
from src.services.oauth_service import OAuthService
from src.api.dependencies.kafka_dependency import get_event_publisher
from src.api.dependencies.token_dependency import get_token_service, get_refresh_token_from_cookie
from src.api.dependencies.user_dependency import get_user_service, get_current_user
from src.api.schemas.token import AccessTokenResponse, SessionInfo
from src.api.schemas.user import UserPublic, UserCreate, UserInternal
from src.core.config import settings
from src.infrastructure.kafka.event_publisher import EventPublisher
from src.infrastructure.redis import get_redis
from src.core.security import decode_refresh_token
from src.services.token_service import TokenService
from src.services.user_service import UserService
from src.utils.cookie_utils import set_refresh_token_in_cookie, delete_old_refresh_token_from_cookie
from src.utils.request_utils import get_client_ip, get_user_agent

auth_router = APIRouter(tags=["Auth"])


@auth_router.post(
    "/register/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    description="Register a new user",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "A user with this name already exists"}
    }
)
async def create_user(
        user_data: UserCreate,
        user_service: Annotated[UserService, Depends(get_user_service)],
        event_publisher: EventPublisher = Depends(get_event_publisher)
) -> UserPublic:
    user_from_db = await user_service.add_user(user_data)

    await event_publisher.publish_user_registered(user_from_db)
    return UserPublic.model_validate(user_from_db)


@auth_router.post(
    "/login/",
    description="Creating access and refresh tokens",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User successfully logged in"},
        404: {"description": "User not found"},
        401: {"description": "Invalid password"},
        403: {"description": "Too many login attempts"}
    }
)
async def login(
        user_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        user_service: Annotated[UserService, Depends(get_user_service)],
        token_service: Annotated[TokenService, Depends(get_token_service)],
        redis: Annotated[Redis, Depends(get_redis)],
        request: Request,
        response: Response
) -> AccessTokenResponse:
    """Fetches email from username field"""
    user_dict = await user_service.authenticate_user(
        user_data.username, user_data.password, redis
    )
    user_dto = UserInternal.model_validate(user_dict)

    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    access_token, refresh_token = await token_service.generate_tokens(
        user_dto, ip_address, user_agent
    )

    if refresh_token:
        set_refresh_token_in_cookie(response, refresh_token)

    return AccessTokenResponse(access_token=access_token)


@auth_router.post(
    "/refresh/",
    description="Issue new access token and rotate refresh token",
    response_model=AccessTokenResponse
)
async def refresh(
        request: Request,
        response: Response,
        token_service: Annotated[TokenService, Depends(get_token_service)],
        user_service: Annotated[UserService, Depends(get_user_service)],
        refresh_token: Annotated[str, Depends(get_refresh_token_from_cookie)]
) -> AccessTokenResponse:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    payload = decode_refresh_token(refresh_token)
    try:
        user_id: UUID = UUID(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise InvalidTokenException()

    await user_service.check_user_by_id(user_id)

    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    try:
        access_token, new_refresh_token = await token_service.rotate_tokens(
            user_id, refresh_token, ip_address, user_agent
        )
    except (TokenNotFoundException, TokenAlreadyUsedException) as e:
        delete_old_refresh_token_from_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except UserNotFoundException as e:
        delete_old_refresh_token_from_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    if new_refresh_token:
        set_refresh_token_in_cookie(response, new_refresh_token)

    return AccessTokenResponse(access_token=access_token)


@auth_router.get("/sessions/", response_model=list[SessionInfo])
async def get_user_sessions(
        token_service: Annotated[TokenService, Depends(get_token_service)],
        current_user: Annotated[dict[str, Any], Depends(get_current_user)]
) -> list[SessionInfo]:
    tokens = await token_service.get_user_sessions(current_user["id"])
    return [SessionInfo.model_validate(token) for token in tokens]


@auth_router.delete(
    "/logout/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "The session logged out"}})
async def logout_session(
        request: Request,
        response: Response,
        current_user: Annotated[dict[str, Any], Depends(get_current_user)],
        token_service: Annotated[TokenService, Depends(get_token_service)],
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise MissingTokenException()

    try:
        await token_service.logout_one(current_user["id"], refresh_token)
    except TokenNotFoundException:
        pass
    finally:
        delete_old_refresh_token_from_cookie(response)


@auth_router.delete(
    "/logout_all/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "All sessions logged out"}}
)
async def logout_all_sessions(
        response: Response,
        current_user: Annotated[dict[str, Any], Depends(get_current_user)],
        token_service: Annotated[TokenService, Depends(get_token_service)]
):
    await token_service.logout_all(current_user["id"])
    response.delete_cookie("refresh_token")


@auth_router.get(
    "/public_key",
    response_class=Response,
    summary="Get current public key",
    status_code=status.HTTP_200_OK
)
def get_public_key():
    if not settings.public_key_file.exists():
        return Response(content="Public key not found", status_code=404)

    return Response(
        content=settings.public_key,
        media_type="text/plain",
        status_code=status.HTTP_200_OK
    )


@auth_router.get(
    "/google/url",
    response_class=RedirectResponse,
    summary="Redirect to Google for OAuth authentication",
    status_code=status.HTTP_302_FOUND
)
async def get_google_oauth_redirect_uri(
        oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
        redis: Annotated[Redis, Depends(get_redis)]
) -> RedirectResponse:
    """
    Generates a secure redirect URL for Google OAuth
    and stores the state parameter in Redis.
    """
    state = secrets.token_urlsafe(32)
    state_key = f"oauth:state:{state}"
    await redis.set(name=state_key, value="valid", ex=300)
    logger.info(f"State key stored in Redis: {state_key}")
    uri = oauth_service.generate_google_oauth_redirect_uri(state)

    return RedirectResponse(url=uri)


@auth_router.get("/google/callback", response_model=OAuthResponse)
async def handle_google_callback(
        code: Annotated[str, Query()],
        state: Annotated[str, Query()],
        redis: Annotated[Redis, Depends(get_redis)],
        oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
        user_service: Annotated[UserService, Depends(get_user_service)],
        token_service: Annotated[TokenService, Depends(get_token_service)],
        request: Request,
        response: Response
) -> OAuthResponse:
    """
    Handles Google OAuth callback, authenticates the user, and issues tokens.
    """
    state_key = f"oauth:state:{state}"
    logger.info(f"Received state key from URL: {state_key}")
    state_value = await redis.get(state_key)
    if not state_value:
        logger.error(f"State key not found in Redis: {state_key}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter."
        )

    await redis.delete(state_key)

    async with aiohttp.ClientSession() as session:
        user_info, files, refresh_token = await oauth_service.handle_google_callback(
            code=code,
            session=session,
        )

    user_data = await user_service.get_or_create_user(
        user_info=user_info,
        refresh_token=refresh_token
    )
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    user_internal = UserInternal.model_validate(user_data)

    access_token, app_refresh_token = await token_service.generate_tokens(
        user_internal, ip_address, user_agent
    )

    if app_refresh_token:
        set_refresh_token_in_cookie(response, app_refresh_token)

    user_public = UserPublic.model_validate(user_data)

    return OAuthResponse(
        user=user_public,
        files=files,
        access_token=access_token,
        refresh_token=app_refresh_token
    )
