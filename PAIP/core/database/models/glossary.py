"""
PAIP Core Database — Glossary Models.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import Base, BaseModelMixin


class GlossaryTermModel(Base, BaseModelMixin):
    """
    Model for enterprise glossary terms (Thuật ngữ chuyên ngành chuẩn).
    Mapping table: glossary_terms
    """

    __tablename__ = "glossary_terms"

    term: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="Canonical standard term in uppercase/proper form (e.g. 'FPSO', 'PTSC QNG')",
    )

    standard_case: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Standard casing presentation",
    )

    full_name_vi: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Full Vietnamese expansion/definition",
    )

    full_name_en: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Full English expansion/definition",
    )

    domain: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        default="General",
        doc="Industry domain (Offshore, HSEQ, EPC, Corporate, Mechanical...)",
    )

    incorrect_variants: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        doc="Commonly misspelled variants or informal writing (e.g. ['fpso', 'Fpso'])",
    )

    synonyms: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        doc="Valid synonyms or alternative standard names",
    )

    do_not_translate: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Flag telling LLM strictly NOT to translate this term into Vietnamese",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Contextual business explanation for prompt injection",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this term is currently active in the rule engine",
    )

    created_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        doc="User UUID who created this term",
    )
