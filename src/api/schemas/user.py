from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, constr, Field, field_validator, BaseModel, computed_field

from src.api.schemas.base import BaseSchemaOut, BaseSchemaIn
from src.api.schemas.role import PermissionSchema, RoleSchema
from src.core.constants import PASSWORD_DESCRIPTION
from src.utils.password_validators import validate_password_strength


class UserBase(BaseModel):
    first_name: str | None = Field(
        None,
        min_length=3,
        max_length=30,
        description="First name must be between 3 and 30 characters long"
    )
    last_name: str | None = Field(
        None,
        min_length=3,
        max_length=30,
        description="Last name must be between 3 and 30 characters long"
    )
    email: EmailStr
    telephone: str | None = None


class UserCreate(UserBase, BaseSchemaIn):
    password: constr(min_length=8) = Field(description=PASSWORD_DESCRIPTION)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str):
        return validate_password_strength(v)


class UserPublic(UserBase, BaseSchemaOut):
    id: UUID
    created_at: datetime
    google_sub: str | None = None


class UserInternal(UserPublic):
    hashed_password: str | None
    is_active: bool
    roles: list[RoleSchema]
    google_refresh_token: str | None = None

    @computed_field
    @property
    def permissions(self) -> list[PermissionSchema]:
        unique_permissions: dict[int, PermissionSchema] = {}
        for role in self.roles:
            for permission in role.permissions:
                unique_permissions[permission.id] = permission
        return list(unique_permissions.values())

    @property
    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    @property
    def permission_names(self) -> list[str]:
        return [p.name for p in self.permissions]


class UserUpdate(UserBase, BaseSchemaIn):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: constr(min_length=8) | None = Field(
        default=None,
        description=PASSWORD_DESCRIPTION
    )
    telephone: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str):
        return validate_password_strength(v)
