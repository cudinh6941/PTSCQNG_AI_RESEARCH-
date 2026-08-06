"""
PAIP Core Database — Agent Task & History Models.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import Base, BaseModelMixin


class Agent0ProofreadHistoryModel(Base, BaseModelMixin):
    """
    Historical proofreading records executed by Agent 0.
    Mapping table: agent0_proofread_history
    """

    __tablename__ = "agent0_proofread_history"

    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    filename: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Original uploaded filename if processed from file (.docx, .pdf)",
    )

    mode: Mapped[str] = mapped_column(
        String(30),
        default="standard",
        nullable=False,
        doc="Proofreading style mode: standard, formal, strict, legal",
    )

    char_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Character length of input document",
    )

    total_errors: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total errors detected across Rule Engine and LLM",
    )

    score: Mapped[float] = mapped_column(
        Float,
        default=10.0,
        nullable=False,
        doc="Computed quality score on 10.0 scale",
    )

    violations_summary: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        doc="Aggregated error breakdown by type and severity",
    )

    processing_time_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Total round-trip processing time in milliseconds",
    )
