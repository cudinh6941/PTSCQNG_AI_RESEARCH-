"""
Rule Engine — Base Classes & Shared Types.

Định nghĩa các lớp trừu tượng (Abstract) và kiểu dữ liệu dùng chung
cho toàn bộ module Rule Engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .context import RuleContext


# ── Enums ─────────────────────────────────────────────────


class RuleSeverity(str, Enum):
    """Mức độ nghiêm trọng của vi phạm."""
    ERROR = "error"        # Bắt buộc sửa (vi phạm quy chuẩn rõ ràng)
    WARNING = "warning"    # Nhắc nhở (nên sửa nhưng không bắt buộc)
    INFO = "info"          # Thông tin tham khảo


class RuleType(str, Enum):
    """Phân loại nhóm Rule."""
    GLOSSARY = "glossary"           # Level 1: Từ điển & viết tắt
    FORMAT = "format"               # Level 2: Thể thức văn bản
    PROCESS = "process"             # Level 3: Quy trình nghiệp vụ


# ── Data Models ───────────────────────────────────────────


class RuleViolation(BaseModel):
    """Một vi phạm / lỗi cụ thể được phát hiện bởi Rule Engine."""

    rule_id: str = Field(
        description="Mã định danh vi phạm (VD: GLOSSARY_INCORRECT_VARIANT)",
    )
    rule_type: RuleType = Field(
        description="Nhóm rule phát hiện lỗi (glossary / format / process)",
    )
    severity: RuleSeverity = Field(
        default=RuleSeverity.WARNING,
        description="Mức độ nghiêm trọng",
    )
    original_text: str = Field(
        description="Đoạn text gốc vi phạm (VD: 'ptsc-qng')",
    )
    suggested_fix: str = Field(
        description="Gợi ý sửa đúng quy chuẩn (VD: 'PTSC QNG')",
    )
    explanation: str = Field(
        default="",
        description="Giải thích lý do vi phạm",
    )
    position: dict | None = Field(
        default=None,
        description="Vị trí vi phạm: {start_char, end_char, line} (nếu xác định được)",
    )


class DetectedTerm(BaseModel):
    """Một thuật ngữ chuyên ngành được phát hiện trong văn bản."""

    term: str = Field(description="Thuật ngữ chuẩn (VD: 'FPSO')")
    full_name_vi: str = Field(default="", description="Tên đầy đủ tiếng Việt")
    full_name_en: str = Field(default="", description="Tên đầy đủ tiếng Anh")
    domain: str = Field(default="", description="Lĩnh vực")
    description: str = Field(default="", description="Mô tả ngắn")
    do_not_translate: bool = Field(default=False, description="Không được dịch / sửa đổi")


class RuleResult(BaseModel):
    """Kết quả tổng hợp sau khi chạy toàn bộ pipeline Rule Engine."""

    # Danh sách vi phạm phát hiện
    violations: list[RuleViolation] = Field(default_factory=list)

    # Các thuật ngữ chuyên ngành tìm thấy trong bài
    detected_terms: list[DetectedTerm] = Field(default_factory=list)

    # Danh sách từ chuẩn để bảo vệ (LLM không được sửa bậy)
    whitelist_terms: list[str] = Field(default_factory=list)

    # Đoạn text chứa định nghĩa thuật ngữ để bơm vào Prompt LLM
    prompt_injection: str = Field(default="")

    # Thời gian xử lý (milliseconds)
    processing_time_ms: float = Field(default=0.0)

    @property
    def has_violations(self) -> bool:
        """Có vi phạm nào không."""
        return len(self.violations) > 0

    @property
    def error_count(self) -> int:
        """Số lượng vi phạm mức ERROR."""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Số lượng vi phạm mức WARNING."""
        return sum(1 for v in self.violations if v.severity == RuleSeverity.WARNING)


# ── Abstract Base Rule ────────────────────────────────────


class BaseRule(ABC):
    """
    Lớp trừu tượng cho mọi Rule.

    Mỗi Rule cụ thể (GlossaryRule, FormatRule, ProcessRule) phải
    kế thừa từ class này và implement phương thức `evaluate()`.
    """

    def __init__(self, *, enabled: bool = True, severity: RuleSeverity = RuleSeverity.WARNING):
        self.enabled = enabled
        self.default_severity = severity

    @property
    @abstractmethod
    def rule_type(self) -> RuleType:
        """Trả về loại Rule (GLOSSARY, FORMAT, PROCESS)."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Tên hiển thị của Rule."""
        ...

    @abstractmethod
    def evaluate(self, context: RuleContext) -> RuleResult:
        """
        Thực thi đánh giá Rule trên một RuleContext.

        Args:
            context: Ngữ cảnh chứa text và metadata cần kiểm tra.

        Returns:
            RuleResult chứa violations, detected_terms, whitelist, prompt_injection.
        """
        ...
