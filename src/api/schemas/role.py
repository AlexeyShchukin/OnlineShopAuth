from src.api.schemas.base import BaseSchema


class RoleSchema(BaseSchema):
    id: int
    name: str


class PermissionSchema(BaseSchema):
    id: int
    name: str
