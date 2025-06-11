from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, constr, Field

from src.api.schemas.mixins import PasswordValidationMixin
from src.api.schemas.role import PermissionSchema, RoleSchema
from src.core.constants import PASSWORD_DESCRIPTION


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: constr(min_length=3,
                       max_length=30) = Field(description="First_name must be between 3 and 30 characters long")
    last_name: constr(min_length=3,
                      max_length=30) = Field(description="Last_name must be between 3 and 30 characters long")
    email: EmailStr
    telephone: str | None = None


class UserCreate(UserBase, PasswordValidationMixin):
    password: constr(min_length=8) = Field(description=PASSWORD_DESCRIPTION)


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

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


class UserUpdate(BaseModel, PasswordValidationMixin):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: constr(min_length=8) | None = Field(default=None, description=PASSWORD_DESCRIPTION)
    telephone: str | None = None
