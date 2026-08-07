"""
PAIP System Rules Database Model
"""

from typing import Optional
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class SystemRule(Base, TimestampMixin):
    """
    Stores system-wide rules for Glossary, Consistency, Format, and Spelling checking.
    """
    __tablename__ = "system_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    rule_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # 'glossary' | 'consistency' | 'format' | 'spelling'
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # 'HIGH' | 'MEDIUM' | 'LOW'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    config_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Optional JSON serialized parameters
