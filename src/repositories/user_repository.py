from uuid import UUID

from sqlalchemy import select, insert, join, distinct
from sqlalchemy.orm import selectinload

from src.db.models import User, users_roles, Role, roles_permissions, Permission
from src.repositories.base_repository import Repository


class UserRepository(Repository):
    model = User

    async def find_by_email(self, user_email: str):
        stmt = (
            select(self.model)
            .where(self.model.email == user_email)
            .options(selectinload(self.model.roles)
                     .selectinload(Role.permissions)
                     )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: UUID):
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .options(selectinload(self.model.roles)
                     .selectinload(Role.permissions)
                     )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def assign_role(self, user_id: UUID, role_id: int) -> None:
        stmt = insert(users_roles).values(user_id=user_id, role_id=role_id)
        await self.session.execute(stmt)

    async def get_user_permissions(self, user_id: UUID):
        j = (
            join(users_roles, roles_permissions,
                 users_roles.c.role_id == roles_permissions.c.role_id)
            .join(Permission, Permission.id == roles_permissions.c.permission_id)
        )

        stmt = (
            select(distinct(Permission.name))
            .select_from(j)
            .where(users_roles.c.user_id == user_id)
        )

        result = await self.session.execute(stmt)
        return result.all()

    async def get_user_roles(self, user_id: UUID):
        j = join(users_roles, Role, users_roles.c.role_id == Role.id)
        stmt = (
            select(Role.name)
            .select_from(j)
            .where(users_roles.c.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def check_user_by_id(self, user_id: UUID):
        stmt = select(self.model.id, self.model.is_active).where(self.model.id == user_id)
        result = await self.session.execute(stmt)
        return result.one_or_none()
