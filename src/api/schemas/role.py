from src.api.schemas.base import BaseSchemaOut


class RoleSchema(BaseSchemaOut):
    id: int
    name: str
    permissions: list["PermissionSchema"]


class PermissionSchema(BaseSchemaOut):
    id: int
    name: str
