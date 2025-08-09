from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select, delete

from src.db.models import RefreshToken
from src.repositories.base_repository import Repository


class RefreshTokenRepository(Repository):
    model = RefreshToken

    async def find_all_by_user(self, user_id: UUID) -> list[RefreshToken]:
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_token_and_user(
            self, token: str, user_id: UUID
    ) -> RefreshToken | None:
        stmt = select(self.model).where(
            self.model.token == token,
            self.model.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_all_for_user(self, user_id: UUID):
        stmt = delete(self.model).where(self.model.user_id == user_id)
        await self.session.execute(stmt)

    async def delete_expired_and_used_tokens(self):
        stmt = delete(self.model).where(
            self.model.expires_at < datetime.now(timezone.utc)
        )
        await self.session.execute(stmt)

        thirty_seconds_ago = datetime.now(timezone.utc) - timedelta(seconds=30)
        stmt_used = delete(self.model).where(
            self.model.used == True,
            self.model.used_at < thirty_seconds_ago
        )
        await self.session.execute(stmt_used)

    async def delete_by_token_and_user(self, user_id: UUID, token: str) -> int:
        stmt = delete(self.model).where(
            self.model.token == token,
            self.model.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore