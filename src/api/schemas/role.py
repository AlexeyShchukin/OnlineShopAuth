from pydantic import BaseModel


class RoleSchema(BaseModel):
    id: int
    name: str


class PermissionSchema(BaseModel):
    id: int
    name: str
