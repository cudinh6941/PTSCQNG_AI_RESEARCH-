"""
PAIP Core Database — Declarative Base & Universal Mixins.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative Base for all PAIP models."""
    pass


class BaseModelMixin:
    """
    Standard mixin providing:
    - UUID4 string primary key (UUID compatible across SQLite and PostgreSQL)
    - UTC created_at timestamp
    - UTC updated_at timestamp (auto-updates)
    - Serializer to dictionary
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier (UUID v4 string)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
        doc="Record creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
        doc="Record last update timestamp (UTC)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to python dictionary."""
        result: Dict[str, Any] = {}
        for column in self.__table__.columns:
            val = getattr(self, column.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[column.name] = val
        return result
