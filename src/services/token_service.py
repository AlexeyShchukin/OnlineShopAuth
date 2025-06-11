from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from fastapi import Request, HTTPException, Response

from src.api.schemas.token import SessionInfo, AccessTokenResponse
from src.core.security import create_refresh_token, create_access_token
from src.db.models import RefreshToken
from src.loggers.loggers import logger
from src.utils.cookie_utils import set_refresh_cookie
from src.utils.request_utils import get_client_ip, get_user_agent
from src.utils.unit_of_work import IUnitOfWork


class TokenService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    @staticmethod
    async def _save_refresh_token(
            user_id: UUID,
            token: str,
            request: Request,
            uow: IUnitOfWork
    ) -> RefreshToken:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        refresh_token_data = {
            "token": token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "user_id": user_id
        }

        refresh_token = await uow.refresh_tokens.add_one(refresh_token_data)

        return refresh_token

    @staticmethod
    def _delete_refresh_cookie(response: Response) -> None:
        response.delete_cookie("refresh_token", path="/")

    @staticmethod
    async def _mark_token_as_used(token_obj: RefreshToken, uow: IUnitOfWork) -> None:
        token_obj.used = True
        token_obj.used_at = datetime.now(timezone.utc)
        await uow.refresh_tokens.update(token_obj)

    async def get_user_sessions(self, user_id: UUID) -> list[SessionInfo]:
        async with self.uow as uow:
            tokens = await uow.refresh_tokens.find_all_by_user(user_id)
            return [SessionInfo.model_validate(token) for token in tokens]

    async def get_refresh_token_from_db(self, user_id: UUID, refresh_token: str) -> RefreshToken | None:
        async with self.uow as uow:
            token_obj = await uow.refresh_tokens.find_by_token_and_user(refresh_token, user_id)
            if token_obj is None:
                raise HTTPException(status_code=404, detail="Token not found")
            return token_obj

    async def logout_one(self, user_id: UUID, refresh_token: str):
        token_obj = await self.get_refresh_token_from_db(user_id, refresh_token)
        async with self.uow as uow:
            await uow.refresh_tokens.delete(token_obj)
            await uow.commit()

    async def logout_all(self, user_id: UUID) -> None:
        async with self.uow as uow:
            await uow.refresh_tokens.delete_all_for_user(user_id)
            await uow.commit()

    async def cleanup_expired_and_used_sessions(self):
        async with self.uow as uow:
            await uow.refresh_tokens.delete_expired_tokens()
            await uow.commit()

    async def issue_new_refresh_token(
            self,
            user_id: UUID,
            response: Response,
            request: Request,
            uow: IUnitOfWork | None = None
    ) -> str:
        refresh_token = create_refresh_token(
            {
                "sub": str(user_id),
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid4())
            }
        )

        if uow is None:
            async with self.uow as new_uow:
                await self._save_refresh_token(user_id, refresh_token, request, new_uow)
                await new_uow.commit()
        else:
            await self._save_refresh_token(user_id, refresh_token, request, uow)

        set_refresh_cookie(response, refresh_token)

        return refresh_token

    async def rotate_tokens(
            self,
            user_id: UUID,
            refresh_token: str,
            response: Response,
            request: Request
    ) -> AccessTokenResponse:
        """Rotate the refresh token and return a new access token.
        Maintains a 30 s grace period on the old token, invalidates it thereafter."""
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"

        async with self.uow as uow:
            token_obj = await uow.refresh_tokens.find_by_token_and_user(refresh_token, user_id)

            if not token_obj:
                self._delete_refresh_cookie(response)
                logger.warning(f"Unknown refresh token detected for user {user_id}")
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            if token_obj.used_at and token_obj.used_at < datetime.now(timezone.utc) - timedelta(seconds=30):
                self._delete_refresh_cookie(response)
                logger.warning(f"Used refresh token detected for user {user_id}")
                raise HTTPException(status_code=401, detail="Refresh token has been already used")

            role_rows = await uow.users.get_user_roles(user_id)
            perm_rows = await uow.users.get_user_permissions(user_id)
            roles = [r[0] for r in role_rows]
            permissions = [p[0] for p in perm_rows]

            access_token = create_access_token(
                {
                    "sub": str(user_id),
                    "iat": datetime.now(timezone.utc),
                    "jti": str(uuid4()),
                    "roles": roles,
                    "permissions": permissions
                }
            )

            if token_obj.used_at and token_obj.used_at >= datetime.now(timezone.utc) - timedelta(seconds=30):
                return AccessTokenResponse(access_token=access_token)

            await self.issue_new_refresh_token(user_id, response, request, uow)
            await self._mark_token_as_used(token_obj, uow)
            await uow.commit()
            return AccessTokenResponse(access_token=access_token)
