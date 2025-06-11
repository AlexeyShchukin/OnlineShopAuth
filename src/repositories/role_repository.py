from sqlalchemy import select

from src.db.models import Role
from src.repositories.base_repository import Repository


class RoleRepository(Repository):
    model = Role

    async def find_by_name(self, name: str) -> Role | None:
        stmt = select(self.model).where(self.model.name == name)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()