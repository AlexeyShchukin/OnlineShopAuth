from functools import cached_property
from pathlib import Path
from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict


dotenv_path = Path(__file__).parent.parent.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    ACCESS_TOKEN_ALGORITHM: str
    REFRESH_TOKEN_ALGORITHM: str
    REFRESH_TOKEN_SECRET_KEY: str
    PRIVATE_KEY_PATH: str
    PUBLIC_KEY_PATH: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def private_key_file(self) -> Path:
        return Path(self.PRIVATE_KEY_PATH)

    @property
    def public_key_file(self) -> Path:
        return Path(self.PUBLIC_KEY_PATH)

    @cached_property
    def private_key(self) -> str:
        return self.private_key_file.read_text()

    @cached_property
    def public_key(self) -> str:
        return self.public_key_file.read_text()

    def clear_keys_cache(self):
        type(self).private_key.fdel(self)
        type(self).public_key.fdel(self)

    model_config = SettingsConfigDict()


settings = Settings()
