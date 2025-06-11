from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPairResponse(AccessTokenResponse):
    refresh_token: str


class SessionInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    used: bool
    used_at: datetime | None
