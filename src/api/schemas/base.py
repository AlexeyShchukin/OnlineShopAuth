from pydantic import BaseModel, ConfigDict

from src.utils.pydantic_utils import to_lower_camel


class BaseSchemaIn(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_lower_camel,
        populate_by_name=True,
        str_strip_whitespace=True
    )


class BaseSchemaOut(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        from_attributes=True,
        alias_generator=to_lower_camel,
        populate_by_name=True
    )



