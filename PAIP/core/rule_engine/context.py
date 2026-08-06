"""
Rule Engine — Rule Context.

Đóng gói toàn bộ ngữ cảnh (text + metadata) cần thiết
để các Rules đánh giá văn bản.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RuleContext(BaseModel):
    """
    Ngữ cảnh được truyền vào RuleEngine để đánh giá.

    Chứa nội dung văn bản gốc cùng các metadata bổ sung
    để các Rule có thể phân loại & áp dụng logic phù hợp.
    """

    # Nội dung văn bản cần kiểm tra
    text: str = Field(description="Nội dung văn bản cần đánh giá")

    # Metadata bổ sung (optional)
    mode: str = Field(
        default="standard",
        description="Chế độ kiểm tra (standard / formal / strict / legal)",
    )
    department: str | None = Field(
        default=None,
        description="Phòng ban của người dùng (VD: 'HSEQ', 'EPC', 'Procurement')",
    )
    document_type: str | None = Field(
        default=None,
        description="Loại văn bản (VD: 'to_trinh', 'quyet_dinh', 'hop_dong', 'bao_cao')",
    )
    user_id: str | None = Field(
        default=None,
        description="ID người dùng (từ LDAP / Auth)",
    )

    # Flags điều khiển
    enable_glossary: bool = Field(
        default=True,
        description="Bật / tắt kiểm tra từ điển cho request này",
    )
    strict_mode: bool = Field(
        default=False,
        description="True = bắt lỗi nghiêm ngặt (severity=ERROR), False = chỉ nhắc nhở (WARNING)",
    )
