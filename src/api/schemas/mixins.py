from pydantic import field_validator

from src.utils.password_validators import validate_password_strength

class PasswordValidationMixin:
    @field_validator("password")
    @classmethod
    def password_strength(cls, pwd: str) -> str:
        return validate_password_strength(pwd)