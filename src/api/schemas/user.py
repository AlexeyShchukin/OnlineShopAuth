from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, constr, Field, field_validator

from src.api.schemas.base import BaseSchema
from src.api.schemas.role import PermissionSchema, RoleSchema
from src.core.constants import PASSWORD_DESCRIPTION
from src.utils.password_validators import validate_password_strength


class UserBase(BaseSchema):
    first_name: constr(min_length=3,
                       max_length=30) = Field(description="First_name must be between 3 and 30 characters long")
    last_name: constr(min_length=3,
                      max_length=30) = Field(description="Last_name must be between 3 and 30 characters long")
    email: EmailStr
    telephone: str | None = None


class UserCreate(UserBase):
    password: constr(min_length=8) = Field(description=PASSWORD_DESCRIPTION)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str):
        return validate_password_strength(v)

    model_config = ConfigDict(**UserBase.model_config, str_strip_whitespace=True)


class UserPublic(UserBase):
    id: UUID
    created_at: datetime


class UserInternal(UserPublic):
    hashed_password: str
    is_active: bool
    roles: list[RoleSchema]
    permissions: list[PermissionSchema]

    @property
    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    @property
    def permission_names(self) -> list[str]:
        return [p.name for p in self.permissions]


class UserUpdate(BaseSchema):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: constr(min_length=8) | None = Field(default=None, description=PASSWORD_DESCRIPTION)
    telephone: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str):
        return validate_password_strength(v)

    model_config = ConfigDict(**BaseSchema.model_config, str_strip_whitespace=True)
