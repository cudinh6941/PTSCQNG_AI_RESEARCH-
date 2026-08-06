"""
PAIP Core Database — Audit & Telemetry Models.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import Base, BaseModelMixin


class AuditLogModel(Base, BaseModelMixin):
    """
    Audit log model for compliance, security tracking, and configuration changes.
    Mapping table: audit_logs
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        doc="Action executed: CREATE_TERM, UPDATE_TERM, DELETE_TERM, UPDATE_RULE, LOGIN",
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        doc="Entity type: glossary, rule, user, setting",
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Target resource identifier",
    )

    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="State before change",
    )

    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="State after change",
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )


class LLMRequestModel(Base, BaseModelMixin):
    """
    Telemetry model tracking token usage, latency, and costs across all AI Agents.
    Mapping table: llm_requests
    """

    __tablename__ = "llm_requests"

    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    department_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    agent_id: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        doc="Originating agent: agent_0_proofreader, agent_1_meeting...",
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="LLM provider: gemini, openai, claude, local",
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Specific model name (e.g. 'gemini-2.5-flash', 'gpt-4o-mini')",
    )

    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Execution round-trip latency in milliseconds",
    )

    estimated_cost_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Estimated USD cost computed from provider token rates",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="SUCCESS",
        nullable=False,
        doc="SUCCESS, ERROR, TIMEOUT",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


class DepartmentQuotaModel(Base, BaseModelMixin):
    """
    Department monthly AI usage quota and budget limit.
    Mapping table: department_quotas
    """

    __tablename__ = "department_quotas"

    department_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    monthly_budget_usd: Mapped[float] = mapped_column(
        Float,
        default=50.0,
        nullable=False,
    )

    current_month_usage_usd: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    alert_threshold_percent: Mapped[int] = mapped_column(
        Integer,
        default=80,
        nullable=False,
    )

    is_hard_limit: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
