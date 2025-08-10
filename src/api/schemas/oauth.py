from typing import Any

from pydantic import Field

from src.api.schemas.base import BaseSchemaOut
from src.api.schemas.user import UserPublic


class GoogleIdTokenPayload(BaseSchemaOut):
    email: str = Field(...)
    sub: str = Field(..., description="User's unique Google ID.")


class OAuthResponse(BaseSchemaOut):
    user: UserPublic
    files: dict[str, Any] | None = None
    access_token: str
    refresh_token: str
