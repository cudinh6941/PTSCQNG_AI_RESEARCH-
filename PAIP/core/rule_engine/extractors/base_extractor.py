"""
Base Entity Extractor & Data Structures for Consistency Auditing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Các nhóm thực thể cần bóc tách trong văn bản."""
    DOCUMENT_CODE = "document_code"      # Số hiệu VB: 43/TMCG-TKE, QĐ-2026/01
    MONEY = "money"                      # Tiền số & tiền chữ
    DATE = "date"                        # Ngày tháng năm: 06/08/2026, ngày 06 tháng 08 năm 2026
    DURATION = "duration"                # Thời lượng: 3 ngày, 6 tháng, 1 năm
    PERCENTAGE = "percentage"            # Tỷ lệ %: 30%, 50%
    PARTY = "party"                      # Tên đối tác / bên ký


class ExtractedEntity(BaseModel):
    """Một thực thể cụ thể được bóc tách từ văn bản."""

    entity_type: EntityType = Field(description="Loại thực thể")
    raw_text: str = Field(description="Đoạn văn bản thô trích xuất từ tài liệu")
    normalized_value: Any = Field(
        default=None,
        description="Giá trị đã chuẩn hóa (VD: số tiền int/float, đối tượng date, số % float, mã số chuẩn)",
    )
    span: tuple[int, int] = Field(
        default=(0, 0),
        description="Vị trí ký tự bắt đầu và kết thúc (start_char, end_char)",
    )
    line_number: int | None = Field(
        default=None,
        description="Dòng xuất hiện (1-indexed nếu xác định được)",
    )
    context_snippet: str = Field(
        default="",
        description="Đoạn trích ngữ cảnh ngắn xung quanh thực thể",
    )
    section: str = Field(
        default="body",
        description="Phân vùng văn bản: header, body, payment_terms, attachment, appendix, footer",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata bổ sung đặc thù cho từng loại thực thể",
    )


class EntityMatrix(BaseModel):
    """Ma trận thực thể có cấu trúc của toàn bộ văn bản."""

    document_codes: list[ExtractedEntity] = Field(default_factory=list)
    monies: list[ExtractedEntity] = Field(default_factory=list)
    dates: list[ExtractedEntity] = Field(default_factory=list)
    durations: list[ExtractedEntity] = Field(default_factory=list)
    percentages: list[ExtractedEntity] = Field(default_factory=list)
    parties: list[ExtractedEntity] = Field(default_factory=list)

    @property
    def total_entities(self) -> int:
        """Tổng số thực thể trích xuất được."""
        return (
            len(self.document_codes)
            + len(self.monies)
            + len(self.dates)
            + len(self.durations)
            + len(self.percentages)
            + len(self.clause_refs)
            + len(self.parties)
        )


class BaseEntityExtractor(ABC):
    """Lớp cơ sở trừu tượng cho tất cả các Entity Extractor."""

    @property
    @abstractmethod
    def entity_type(self) -> EntityType:
        """Loại thực thể mà extractor này chịu trách nhiệm bóc tách."""
        ...

    @abstractmethod
    def extract(self, text: str) -> list[ExtractedEntity]:
        """
        Bóc tách toàn bộ thực thể thuộc loại này từ văn bản thô.

        Args:
            text: Toàn văn bản cần quét.

        Returns:
            Danh sách ExtractedEntity.
        """
        ...
