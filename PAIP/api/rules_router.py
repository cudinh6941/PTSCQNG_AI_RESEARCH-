"""
Rule Engine — API Router.

Endpoints quản trị Từ điển & Rule Engine:
    GET    /api/v1/rules/glossary          — Lấy danh sách từ điển (search, filter)
    GET    /api/v1/rules/glossary/{term}   — Lấy chi tiết 1 thuật ngữ
    POST   /api/v1/rules/glossary          — Thêm từ mới
    PUT    /api/v1/rules/glossary/{term}   — Cập nhật từ
    DELETE /api/v1/rules/glossary/{term}   — Xóa từ
    POST   /api/v1/rules/reload            — Hot-reload Rule Engine
    POST   /api/v1/rules/test              — Test thử Rule Engine trên văn bản mẫu
    GET    /api/v1/rules/stats             — Thống kê Rule Engine
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.rule_engine import RuleContext, rule_engine
from core.rule_engine.loaders.json_loader import GlossaryItem

router = APIRouter(prefix="/api/v1/rules", tags=["Rule Engine — Quản Trị Từ Điển & Quy Chuẩn"])


# ── Request / Response Schemas ────────────────────────────


class GlossaryCreateRequest(BaseModel):
    """Request tạo mới một thuật ngữ."""
    term: str = Field(description="Thuật ngữ chuẩn (VD: 'FPSO')")
    full_name_en: str = Field(default="", description="Tên đầy đủ tiếng Anh")
    full_name_vi: str = Field(default="", description="Tên đầy đủ tiếng Việt")
    domain: str = Field(default="General", description="Lĩnh vực")
    standard_case: str = Field(default="", description="Cách viết chuẩn")
    incorrect_variants: list[str] = Field(default_factory=list, description="Các biến thể sai")
    synonyms: list[str] = Field(default_factory=list, description="Từ đồng nghĩa")
    do_not_translate: bool = Field(default=False, description="Không được dịch")
    description: str = Field(default="", description="Mô tả ngắn")


class GlossaryUpdateRequest(BaseModel):
    """Request cập nhật thuật ngữ (chỉ gửi các trường cần sửa)."""
    full_name_en: str | None = None
    full_name_vi: str | None = None
    domain: str | None = None
    standard_case: str | None = None
    incorrect_variants: list[str] | None = None
    synonyms: list[str] | None = None
    do_not_translate: bool | None = None
    description: str | None = None


class RuleTestRequest(BaseModel):
    """Request test thử Rule Engine."""
    text: str = Field(description="Văn bản mẫu cần kiểm tra")
    mode: str = Field(default="standard", description="Chế độ kiểm tra")
    department: str | None = Field(default=None, description="Phòng ban")
    strict_mode: bool = Field(default=False, description="Bật chế độ nghiêm ngặt")


# ── Endpoints ─────────────────────────────────────────────


@router.get("/glossary")
async def list_glossary(
    query: str = Query(default="", description="Từ khóa tìm kiếm"),
    domain: str | None = Query(default=None, description="Lọc theo lĩnh vực"),
):
    """Lấy danh sách từ điển. Hỗ trợ tìm kiếm và lọc theo lĩnh vực."""
    items = rule_engine.search_glossary(query=query, domain=domain)
    return {
        "total": len(items),
        "items": [item.model_dump() for item in items],
    }


@router.get("/glossary/{term}")
async def get_glossary_term(term: str):
    """Lấy chi tiết một thuật ngữ."""
    item = rule_engine.get_glossary_term(term)
    if not item:
        raise HTTPException(status_code=404, detail=f"Thuật ngữ '{term}' không tồn tại.")
    return item.model_dump()


@router.post("/glossary", status_code=201)
async def create_glossary_term(request: GlossaryCreateRequest):
    """Thêm một thuật ngữ mới vào kho từ điển."""
    item = GlossaryItem(
        term=request.term,
        full_name_en=request.full_name_en,
        full_name_vi=request.full_name_vi,
        domain=request.domain,
        standard_case=request.standard_case or request.term,
        incorrect_variants=request.incorrect_variants,
        synonyms=request.synonyms,
        do_not_translate=request.do_not_translate,
        description=request.description,
    )
    try:
        created = rule_engine.add_glossary_term(item)
        return {
            "message": f"Đã thêm thuật ngữ '{created.term}' thành công.",
            "item": created.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/glossary/{term}")
async def update_glossary_term(term: str, request: GlossaryUpdateRequest):
    """Cập nhật một thuật ngữ đã có."""
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Không có trường nào cần cập nhật.")
    try:
        updated = rule_engine.update_glossary_term(term, updates)
        return {
            "message": f"Đã cập nhật thuật ngữ '{term}' thành công.",
            "item": updated.model_dump(),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/glossary/{term}")
async def delete_glossary_term(term: str):
    """Xóa một thuật ngữ khỏi kho."""
    success = rule_engine.delete_glossary_term(term)
    if not success:
        raise HTTPException(status_code=404, detail=f"Thuật ngữ '{term}' không tồn tại.")
    return {"message": f"Đã xóa thuật ngữ '{term}' thành công."}


@router.post("/reload")
async def reload_rules():
    """Hot-reload: Nạp lại toàn bộ dữ liệu Rule Engine mà không cần restart server."""
    result = rule_engine.reload()
    return {
        "message": "Đã nạp lại Rule Engine thành công.",
        **result,
    }


@router.post("/test")
async def test_rules(request: RuleTestRequest):
    """Test thử Rule Engine trên một đoạn văn bản mẫu (không gọi LLM)."""
    context = RuleContext(
        text=request.text,
        mode=request.mode,
        department=request.department,
        strict_mode=request.strict_mode,
    )
    result = rule_engine.evaluate(context)
    return {
        "processing_time_ms": round(result.processing_time_ms, 2),
        "violations": [v.model_dump() for v in result.violations],
        "detected_terms": [dt.model_dump() for dt in result.detected_terms],
        "whitelist_terms": result.whitelist_terms,
        "prompt_injection_preview": result.prompt_injection[:500] if result.prompt_injection else "",
    }


@router.get("/stats")
async def get_stats():
    """Thống kê tổng quan Rule Engine."""
    all_items = rule_engine.get_all_glossary_terms()
    domains: dict[str, int] = {}
    for item in all_items:
        domains[item.domain] = domains.get(item.domain, 0) + 1

    return {
        "is_loaded": rule_engine.is_loaded,
        "total_glossary_terms": rule_engine.glossary_count,
        "domains": domains,
    }
