from src.core.config import settings
from src.db.database import Base
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import DateTime, String, ForeignKey, Index, Table, Column, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    first_name: Mapped[str] = mapped_column(String(30), unique=False, nullable=True)
    last_name: Mapped[str] = mapped_column(String(30), unique=False, nullable=True)
    email: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=True)
    telephone: Mapped[str] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    google_sub: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    google_refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        secondary="users_roles",
        back_populates="users"
    )

    tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user"
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_dict_with_relations(self, relations_to_include=None):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}

        if relations_to_include:
            for relation_name in relations_to_include:
                related_obj = getattr(self, relation_name)
                if related_obj:
                    if isinstance(related_obj, list):
                        data[relation_name] = [item.to_dict() for item in related_obj]
                    else:
                        data[relation_name] = related_obj.to_dict()
        return data


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(String(100), nullable=True)

    users: Mapped[list["User"]] = relationship(
        secondary="users_roles",
        back_populates="roles"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="roles_permissions",
        back_populates="roles"
    )

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}

        data["permissions"] = [p.to_dict() for p in self.permissions]
        return data


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str] = mapped_column(String(100), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        secondary="roles_permissions",
        back_populates="permissions"
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


users_roles = Table(
    "users_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

roles_permissions = Table(
    "roles_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(200))
    used: Mapped[bool] = mapped_column(default=False)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    __table_args__ = (Index('ix_refresh_tokens_token_user', 'token', 'user_id'),)

    user: Mapped["User"] = relationship("User", back_populates="tokens")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, expires_at={self.expires_at})>"
