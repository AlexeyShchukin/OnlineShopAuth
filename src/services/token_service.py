from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID, uuid4

from src.api.schemas.user import UserInternal
from src.core.security import create_refresh_token, create_access_token
from src.db.models import RefreshToken
from src.exceptions.service_exceptions import (
    TokenAlreadyUsedException,
    TokenNotFoundException,
    UserNotFoundException
)
from src.loggers.loggers import logger
from src.utils.unit_of_work import IUnitOfWork


class TokenService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def get_user_sessions(self, user_id: UUID) -> list[dict[str, Any]]:
        async with self.uow as uow:
            tokens = await uow.refresh_tokens.find_all_by_user(user_id)
            return [token.to_dict() for token in tokens]

    async def logout_one(self, user_id: UUID, refresh_token: str):
        async with self.uow as uow:
            rows_deleted = await uow.refresh_tokens.delete_by_token_and_user(
                user_id, refresh_token
            )
            if rows_deleted == 0:
                raise TokenNotFoundException()
            await uow.commit()

    async def logout_all(self, user_id: UUID) -> None:
        async with self.uow as uow:
            await uow.refresh_tokens.delete_all_for_user(user_id)
            await uow.commit()

    async def cleanup_expired_and_used_sessions(self):
        async with self.uow as uow:
            await uow.refresh_tokens.delete_expired_tokens()
            await uow.commit()

    async def generate_tokens(
            self,
            user: UserInternal,
            ip_address: str | None,
            user_agent: str | None
    ) -> tuple[str, str]:
        """
        Generates access and refresh tokens for a given user.
        """
        user_roles = [role.name for role in user.roles]
        user_permissions = list(set([
            permission.name
            for role in user.roles
            for permission in role.permissions
        ]))

        access_token = create_access_token(
            {"sub": str(user.id),
             "iat": datetime.now(timezone.utc),
             "jti": str(uuid4()),
             "roles": user_roles,
             "permissions": user_permissions
             }
        )

        async with self.uow as uow:
            app_refresh_token = await self._create_and_save_new_refresh_token(
                user.id, ip_address, user_agent, uow
            )
            await uow.commit()

        return access_token, app_refresh_token

    async def rotate_tokens(
            self,
            user_id: UUID,
            refresh_token: str,
            ip_address: str | None,
            user_agent: str | None
    ) -> tuple[str, str]:
        """
        Rotate the refresh token and return a new access token.
        Maintains a 30 s grace period on the old token, invalidates it thereafter.
        """
        async with self.uow as uow:
            token_obj = await uow.refresh_tokens.find_by_token_and_user(
                refresh_token, user_id
            )

            if not token_obj:
                logger.warning(f"Unknown refresh token detected for user {user_id}")
                raise TokenNotFoundException()

            now = datetime.now(timezone.utc)
            grace_period = timedelta(seconds=30)

            if token_obj.used and (now - token_obj.used_at) > grace_period:
                logger.warning(f"Used refresh token detected for user {user_id}")
                raise TokenAlreadyUsedException()

            user_data = await self._get_user_permissions_and_roles(user_id, uow)

            access_token = create_access_token(
                {
                    "sub": str(user_id),
                    "iat": now,
                    "jti": str(uuid4()),
                    "roles": user_data["roles"],
                    "permissions": user_data["permissions"]
                }
            )

            await self._mark_token_as_used(token_obj)
            new_refresh_token_str = await self._create_and_save_new_refresh_token(
                user_id, ip_address, user_agent, uow
            )
            await uow.commit()

            return access_token, new_refresh_token_str

    @staticmethod
    async def _get_user_permissions_and_roles(
            user_id: UUID, uow: IUnitOfWork
    ) -> dict[str, Any]:
        user_from_db = await uow.users.find_by_id(user_id)

        if not user_from_db:
            raise UserNotFoundException()

        roles = [role.name for role in user_from_db.roles]
        permissions = list(
            set([p.name for r in user_from_db.roles for p in r.permissions])
        )

        return {"roles": roles, "permissions": permissions}

    @staticmethod
    async def _mark_token_as_used(token_obj: RefreshToken) -> None:
        token_obj.used = True
        token_obj.used_at = datetime.now(timezone.utc)

    @staticmethod
    async def _create_and_save_new_refresh_token(
            user_id: UUID,
            ip_address: str | None,
            user_agent: str | None,
            uow: IUnitOfWork
    ) -> str:
        """
        Generates and saves a new refresh token within the current transaction.
        """
        new_refresh_token_str = create_refresh_token(
            {
                "sub": str(user_id),
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid4())
            }
        )

        refresh_token_data = {
            "token": new_refresh_token_str,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "user_id": user_id
        }

        await uow.refresh_tokens.add_one(refresh_token_data)

        return new_refresh_token_str
