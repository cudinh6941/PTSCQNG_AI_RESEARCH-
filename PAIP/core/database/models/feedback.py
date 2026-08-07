"""
PAIP Feedback, Correction & Experience Memory Database Models
"""

from typing import Optional
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class UserFeedback(Base, TimestampMixin):
    """
    Stores individual user actions on detected errors (accept / reject / modify / whitelist).
    """
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    history_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    error_original: Mapped[str] = mapped_column(Text, nullable=False)
    error_suggested: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[str] = mapped_column(String(50), default="spelling")
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # 'accept' | 'reject' | 'modify' | 'whitelist'
    user_correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), default="anonymous_user", index=True)


class UserCorrection(Base, TimestampMixin):
    """
    Stores reports from users when AI missed an error (False Negative / Dạy AI).
    """
    __tablename__ = "user_corrections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    error_text: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_fix: Mapped[str] = mapped_column(Text, nullable=False)
    error_category: Mapped[str] = mapped_column(String(50), default="spelling")  # 'spelling' | 'glossary' | 'consistency' | 'format' | 'legal'
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # 'pending' | 'verified' | 'promoted' | 'rejected'
    verified_count: Mapped[int] = mapped_column(Integer, default=1)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), default="anonymous_user", index=True)


class ExperienceMemory(Base, TimestampMixin):
    """
    Stores high-confidence correction examples for dynamic Few-shot prompt injection.
    """
    __tablename__ = "experience_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    category: Mapped[str] = mapped_column(String(50), index=True, default="spelling")  # 'glossary' | 'consistency' | 'legal' | 'format' | 'spelling'
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, default=1.0)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
