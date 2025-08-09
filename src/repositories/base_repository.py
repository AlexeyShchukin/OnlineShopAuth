from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):
    @abstractmethod
    async def add_one(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 10):
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, uuid_: UUID):
        raise NotImplementedError

    @abstractmethod
    async def update_one(self, instance, data: dict):
        raise NotImplementedError

    @abstractmethod
    async def delete_one(self, instance):
        raise NotImplementedError


class Repository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict):
        stmt = insert(self.model).values(**data).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_all(
            self,
            user_id: UUID | None = None,
            skip: int = 0,
            limit: int = 10
    ):
        stmt = select(self.model).offset(skip).limit(limit)

        if user_id is not None:
            stmt = stmt.where(self.model.id == user_id)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_id(self, user_id: UUID):
        stmt = select(self.model).where(self.model.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_one(self, item_id: UUID, data: dict) -> None:
        stmt = update(self.model).where(self.model.id == item_id).values(**data)
        await self.session.execute(stmt)

    async def delete_one(self, item_id: UUID) -> None:
        stmt = delete(self.model).where(self.model.id == item_id)
        await self.session.execute(stmt)
