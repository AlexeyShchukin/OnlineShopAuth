from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.utils.pydantic_utils import to_lower_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        alias_generator=to_lower_camel,
        populate_by_name=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
        },
    )
