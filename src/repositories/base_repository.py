from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select, insert
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


class Repository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict):
        stmt = insert(self.model).values(**data).returning(self.model)
        res = await self.session.execute(stmt)
        return res.scalar_one()

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

    async def delete(self, instance):
        await self.session.delete(instance)

    def update(self, instance, data: dict):
        for field, value in data.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
        return instance
