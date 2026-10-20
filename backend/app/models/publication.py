from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import User


class PublicationType(str, Enum):
    STARTUP = "startup"
    VACANCY = "vacancy"


class PublicationStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class Publication(Base):
    __tablename__ = "publications"

    author: Mapped[User] = relationship(lazy="joined")

    @property
    def author_name(self) -> str:
        return self.author.name

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[PublicationType] = mapped_column(
        SqlEnum(PublicationType, name="publication_type"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    looking_for: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[PublicationStatus] = mapped_column(
        SqlEnum(PublicationStatus, name="publication_status"),
        default=PublicationStatus.ACTIVE,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
