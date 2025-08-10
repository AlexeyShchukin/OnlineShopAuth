from typing import Any
from uuid import UUID

from redis.asyncio import Redis

from src.api.schemas.user import UserCreate, UserUpdate
from src.core.security import hash_password, verify_password, get_user_id_from_token
from src.db.models import User
from src.exceptions.service_exceptions import (
    BlockedUserException,
    InactiveUserException,
    InvalidPasswordException,
    TooManyAttemptsException,
    UserNotFoundException,
    UserAlreadyExistsException,
    ServiceException
)
from src.infrastructure.kafka import event_publisher
from src.infrastructure.kafka.event_publisher import EventPublisher
from src.services.rate_limiter import LoginRateLimiter
from src.utils.unit_of_work import IUnitOfWork


class UserService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def add_user(self, user: UserCreate) -> dict[str, Any]:
        async with self.uow as uow:
            if not await uow.users.find_by_email(user.email):
                hashed_password = hash_password(user.password)
                user_dict = user.model_dump(exclude={"password"})
                user_dict["hashed_password"] = hashed_password
                user_from_db = await uow.users.add_one(user_dict)

                await self._assign_default_role(uow, user_from_db)

                return user_from_db.to_dict()
            raise UserAlreadyExistsException()

    async def authenticate_user(
            self, email: str, password: str, redis: Redis
    ) -> dict[str, Any]:
        """
        Authenticates a user by email and password,
        applying rate-limiting checks.
        """
        limiter = LoginRateLimiter(redis)

        if await limiter.is_blocked(email):
            raise BlockedUserException()

        async with self.uow as uow:
            user_from_db = await uow.users.find_by_email(email)

            if not user_from_db:
                raise UserNotFoundException()

            if not user_from_db.is_active:
                raise InactiveUserException()

            if not verify_password(password, user_from_db.hashed_password):
                attempts = await limiter.incr_attempts(email)
                remaining = limiter.max_attempts - attempts
                if remaining > 0:
                    raise InvalidPasswordException(
                        f"Invalid password. {remaining} login attempts remaining.",
                        remaining_attempts=remaining
                    )

                else:
                    raise TooManyAttemptsException()

            await limiter.reset_attempts(email)
            user_data = self._get_user_data_with_roles_and_permissions(user_from_db)

        return user_data

    async def find_user_by_id(self, user_id: UUID) -> dict[str, Any]:
        async with self.uow as uow:
            user_from_db = await uow.users.find_by_id(user_id)
            if not user_from_db:
                raise UserNotFoundException()
            return user_from_db.to_dict()

    async def check_user_by_id(self, user_id: UUID) -> None:
        async with self.uow as uow:
            user = await uow.users.check_user_by_id(user_id)
            if not user:
                raise UserNotFoundException()
            if not user.is_active:
                raise InactiveUserException()

    async def update_user(
            self, user_update: UserUpdate, token: str
    ) -> dict[str, Any]:
        async with self.uow as uow:
            user_id = get_user_id_from_token(token)

            user_from_db = await uow.users.find_by_id(user_id)
            if not user_from_db:
                raise UserNotFoundException()
            if not user_from_db.is_active:
                raise InactiveUserException()

            data = user_update.model_dump(exclude_unset=True)

            if "email" in data and data["email"] != user_from_db.email:
                if await uow.users.find_by_email(data["email"]):
                    raise UserAlreadyExistsException()

            for field, value in data.items():
                setattr(user_from_db, field, value)

            user = user_from_db.to_dict()

            return user

    async def get_or_create_user(
            self,
            event_publisher: EventPublisher,
            user_info: dict,
            refresh_token: str
    ) -> dict[str, Any]:
        """
        Retrieves a user by Google sub or email, or creates a new one.
        """
        async with self.uow as uow:
            user = await uow.users.find_by_google_sub(user_info["sub"])

            if user:
                if user.google_refresh_token != refresh_token:
                    user.google_refresh_token = refresh_token
                    uow.session.add(user)
                return self._get_user_data_with_roles_and_permissions(user)

            user = await uow.users.find_by_email(user_info["email"])

            if user:
                user.google_sub = user_info["sub"]
                user.google_refresh_token = refresh_token
                uow.session.add(user)
                return self._get_user_data_with_roles_and_permissions(user)

            new_user_data = {
                "email": user_info["email"],
                "first_name": user_info.get("given_name"),
                "last_name": user_info.get("family_name"),
                "google_sub": user_info["sub"],
                "google_refresh_token": refresh_token,
                "hashed_password": None,
            }
            new_user = await uow.users.add_one(new_user_data)
            await self._assign_default_role(uow, new_user)

            user_with_relations = await uow.users.find_by_id(new_user.id)
            user_dict = self._get_user_data_with_roles_and_permissions(user_with_relations)

            await event_publisher.publish_user_registered(user_dict)

            return user_dict

    @staticmethod
    def _get_user_data_with_roles_and_permissions(user: User) -> dict[str, Any]:
        user_data = user.to_dict_with_relations(
            relations_to_include=["roles"]
        )

        all_permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                all_permissions.add(frozenset(permission.to_dict().items()))

        user_data['permissions'] = [dict(fs) for fs in all_permissions]
        return user_data

    @staticmethod
    async def _assign_default_role(uow: IUnitOfWork, user: User) -> None:
        default_role = await uow.roles.find_by_name("customer")
        if not default_role:
            raise ServiceException("Default 'customer' role not found in database.")
        await uow.users.assign_role(user, default_role)
