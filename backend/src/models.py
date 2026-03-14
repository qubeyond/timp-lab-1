import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Content

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Metainfo

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    last_login: Mapped[datetime | None] = mapped_column(
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
    )

    # Relationships

    posts: Mapped[list[Post]] = relationship(
        back_populates="owner",
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    # Content

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        String(500),
    )

    # Metainfo

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_published: Mapped[bool] = mapped_column(
        default=True,
    )

    # Relationships

    owner: Mapped[User] = relationship(
        back_populates="posts",
    )
