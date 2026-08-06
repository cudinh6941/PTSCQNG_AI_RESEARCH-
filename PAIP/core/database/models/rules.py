"""
PAIP Core Database — System Rules & Settings Models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import Base, BaseModelMixin, _utcnow


class SystemRuleModel(Base, BaseModelMixin):
    """
    Model for extensible system rules (Level 2 & Level 3).
    Mapping table: system_rules
    """

    __tablename__ = "system_rules"

    rule_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique rule code (e.g. 'ND30_HEADER_FORMAT', 'AUTH_LIMIT_CHECK')",
    )

    rule_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="Rule categorization: GLOSSARY, FORMAT, PROCESS",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Human-readable rule name",
    )

    config_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        doc="Dynamic configuration parameters for this rule",
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        default="WARNING",
        nullable=False,
        doc="Severity level: INFO, WARNING, ERROR",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        doc="Execution priority order (lower number = higher priority)",
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Toggle to activate or deactivate rule",
    )


class SystemSettingModel(Base):
    """
    Model for dynamic key-value system settings.
    Mapping table: system_settings
    """

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        doc="Configuration key identifier (e.g. 'DEFAULT_LLM_MODEL')",
    )

    value_json: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        doc="Setting value stored as JSON",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Setting purpose and usage note",
    )

    updated_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        doc="User UUID who last updated this setting",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
