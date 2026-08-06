"""
Rule Engine — Core Module.

Cung cấp Rule Engine dùng chung cho toàn bộ PAIP:
- Kiểm tra từ điển & thuật ngữ chuẩn (Glossary Rule).
- Bảo vệ thuật ngữ chuyên ngành khỏi LLM hallucination (Whitelist & Prompt Injection).
- (Future) Kiểm tra thể thức văn bản & tuân thủ quy trình.

Usage:
    from core.rule_engine import rule_engine
    from core.rule_engine.context import RuleContext

    context = RuleContext(text="Văn bản cần kiểm tra...")
    result = rule_engine.evaluate(context)
"""

from .base import (
    BaseRule,
    DetectedTerm,
    RuleResult,
    RuleSeverity,
    RuleType,
    RuleViolation,
)
from .context import RuleContext
from .engine import RuleEngine, rule_engine

__all__ = [
    # Core Engine
    "RuleEngine",
    "rule_engine",
    # Context
    "RuleContext",
    # Base Types
    "BaseRule",
    "RuleResult",
    "RuleViolation",
    "DetectedTerm",
    "RuleSeverity",
    "RuleType",
]
