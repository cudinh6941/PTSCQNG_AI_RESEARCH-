"""
Agent 0 — Schemas (Input/Output models).

Thiết kế dựa trên spec Obsidian:
    PTSC_AI_RnD/Architecture/Agent_Catalog/Agent_0_Document_Proofreader.md
"""

from enum import Enum

from pydantic import BaseModel, Field

from core.common.schemas import AIRequest, AIResponse
from core.scoring import QualityScoreBreakdown


# ── Enums ─────────────────────────────────────────────────

class ErrorType(str, Enum):
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    WORD_CHOICE = "word_choice"
    PUNCTUATION = "punctuation"
    LEGAL = "legal"
    GLOSSARY = "glossary"
    CONSISTENCY = "consistency"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ── Request ───────────────────────────────────────────────

class ProofreadRequest(AIRequest):
    """Request để kiểm tra chính tả & pháp lý."""
    document_text: str = Field(
        default="",
        description="Nội dung văn bản cần kiểm tra",
    )
    mode: str = Field(
        default="standard",
        description="Chế độ kiểm tra: standard (tiêu chuẩn) | formal (trang trọng) | strict (chặt chẽ) | legal (thẩm định pháp lý & tra cứu luật)",
    )
    custom_instructions: str | None = Field(
        default=None,
        description="Ghi chú / yêu cầu đặc biệt từ người dùng cho AI",
    )


class ExportDocxRequest(BaseModel):
    """Request để xuất văn bản ra file Word (.docx)."""
    text: str = Field(..., description="Nội dung văn bản cần xuất")
    filename: str = Field(default="van_ban_hoan_chinh.docx", description="Tên file khi tải về")
    title: str | None = Field(default=None, description="Tiêu đề văn bản (nếu có)")



# ── Response ──────────────────────────────────────────────

class ProofreadError(BaseModel):
    """Một lỗi hoặc điểm cảnh báo được phát hiện."""
    type: ErrorType = Field(default=ErrorType.SPELLING, description="Loại lỗi")
    original: str = Field(default="", description="Đoạn text gốc có lỗi hoặc viện dẫn sai")
    suggested: str = Field(default="", description="Gợi ý sửa hoặc viện dẫn đúng")
    explanation: str = Field(default="", description="Giải thích lý do")
    severity: Severity = Field(default=Severity.MEDIUM, description="Mức độ nghiêm trọng")
    source_link: str | None = Field(default=None, description="Đường dẫn nguồn pháp lý / văn bản đối chiếu (nếu có)")
    reference: str | None = Field(default=None, description="Tên số hiệu văn bản pháp lý trích dẫn (nếu có)")
    side_a: dict | None = Field(default=None, description="Vế A trong đối soát bất nhất")
    side_b: dict | None = Field(default=None, description="Vế B trong đối soát bất nhất")


class ProofreadResult(BaseModel):
    """Kết quả kiểm tra."""
    total_errors: int = Field(default=0, description="Tổng số lỗi")
    errors: list[ProofreadError] = Field(default_factory=list, description="Danh sách lỗi")
    summary: str = Field(default="", description="Tóm tắt chất lượng")
    score: float = Field(default=0.0, description="Điểm chất lượng (1-10)")
    score_breakdown: QualityScoreBreakdown | None = Field(default=None, description="Bảng phân rã điểm 4 trụ cột")



class ProofreadResponse(AIResponse):
    """Response trả về cho client."""
    result: ProofreadResult | None = Field(default=None, description="Kết quả kiểm tra")
    extracted_text: str | None = Field(default=None, description="Nội dung text đã trích xuất từ file (nếu upload)")
    format_report: dict | None = Field(default=None, description="Báo cáo vi phạm thể thức, căn lề, font chữ (file Word)")


