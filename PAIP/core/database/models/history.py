"""
PAIP Proofread History Database Model
"""

from typing import Optional
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class ProofreadHistory(Base, TimestampMixin):
    """
    Stores audit logs and score metrics for each document proofreading execution.
    """
    __tablename__ = "proofread_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    input_type: Mapped[str] = mapped_column(String(20), default="text")  # 'text' | 'file'
    overall_score: Mapped[float] = mapped_column(Float, default=10.0)
    spelling_score: Mapped[float] = mapped_column(Float, default=10.0)
    format_score: Mapped[float] = mapped_column(Float, default=10.0)
    glossary_score: Mapped[float] = mapped_column(Float, default=10.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=10.0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), default="anonymous_user", index=True)
