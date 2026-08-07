"""
Base Auditor & Conflict Data Structures for Cross-Auditing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix


class AuditConflict(BaseModel):
    """Một xung đột / mâu thuẫn bất nhất thông tin được phát hiện bởi Auditor."""

    rule_id: str = Field(description="Mã định danh quy tắc (VD: CA-001, CA-002)")
    rule_name: str = Field(description="Tên quy tắc (VD: Document Code Consistency)")
    severity: RuleSeverity = Field(
        default=RuleSeverity.ERROR,
        description="Mức độ nghiêm trọng (ERROR: bắt buộc sửa, WARNING: cảnh báo)",
    )
    description: str = Field(
        description="Mô tả tóm tắt điểm xung đột",
    )
    original_text: str = Field(
        description="Đoạn văn bản gây xung đột cần bôi sáng trên bài",
    )
    suggested_fix: str = Field(
        default="",
        description="Gợi ý sửa đổi",
    )
    explanation: str = Field(
        default="",
        description="Giải thích chi tiết nguyên nhân bất nhất",
    )
    side_a: dict[str, Any] = Field(
        default_factory=dict,
        description="Dữ liệu Vế A (VD: {'label': 'Bằng số', 'value': '150.000.000 VNĐ', 'section': 'body'})",
    )
    side_b: dict[str, Any] = Field(
        default_factory=dict,
        description="Dữ liệu Vế B (VD: {'label': 'Bằng chữ', 'value': 'Một trăm năm mươi hai triệu đồng', 'section': 'body'})",
    )
    span: tuple[int, int] = Field(
        default=(0, 0),
        description="Tọa độ ký tự trong văn bản",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata bổ sung",
    )


class BaseAuditor(ABC):
    """Lớp cơ sở trừu tượng cho mọi bộ đối soát chéo (Auditor)."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Mã quy tắc đối soát (VD: CA-001)."""
        ...

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Tên quy tắc đối soát."""
        ...

    @abstractmethod
    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        """
        Thực hiện đối soát chéo trên Ma trận Thực thể.

        Args:
            matrix: EntityMatrix chứa các thực thể đã bóc tách.
            full_text: Toàn bộ văn bản gốc (nếu cần tra cứu thêm ngữ cảnh).

        Returns:
            Danh sách các AuditConflict tìm thấy.
        """
        ...
