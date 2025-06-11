from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings

engine = create_async_engine(
    url=settings.ASYNC_DATABASE_URL,
    echo=False
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)


class Base(DeclarativeBase):
    __abstract__ = True

    def __repr__(self):
        table = self.__class__.__name__
        fields = ", ".join(f"{key}={getattr(self, key)!r}" for key in self.__table__.columns.keys())
        return f"<{table}({fields})>"

    def __str__(self):
        return self.__repr__()