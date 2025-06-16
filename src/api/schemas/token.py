from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.api.schemas.base import BaseSchema


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionInfo(BaseSchema):
    id: UUID
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    used: bool
    used_at: datetime | None
