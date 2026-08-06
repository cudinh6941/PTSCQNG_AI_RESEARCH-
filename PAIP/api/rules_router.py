"""
Rule Engine — API Router (Database Persisted).

Endpoints quản trị Từ điển & Rule Engine:
    GET    /api/v1/rules/glossary          — Lấy danh sách từ điển (search, filter)
    GET    /api/v1/rules/glossary/{term}   — Lấy chi tiết 1 thuật ngữ
    POST   /api/v1/rules/glossary          — Thêm từ mới (Ghi CSDL + Auto-reload RAM)
    PUT    /api/v1/rules/glossary/{term}   — Cập nhật từ (Ghi CSDL + Auto-reload RAM)
    DELETE /api/v1/rules/glossary/{term}   — Xóa từ (Ghi CSDL + Auto-reload RAM)
    POST   /api/v1/rules/reload            — Hot-reload Rule Engine từ CSDL
    POST   /api/v1/rules/test              — Test thử Rule Engine trên văn bản mẫu
    GET    /api/v1/rules/stats             — Thống kê Rule Engine
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.engine import get_db
from core.database.models.glossary import GlossaryTermModel
from core.rule_engine import RuleContext, rule_engine

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
    """Lấy danh sách từ điển từ RAM (siêu tốc < 1ms). Hỗ trợ tìm kiếm và lọc."""
    items = rule_engine.search_glossary(query=query, domain=domain)
    return {
        "total": len(items),
        "items": [item.model_dump() for item in items],
    }


@router.get("/glossary/{term}")
async def get_glossary_term(term: str):
    """Lấy chi tiết một thuật ngữ từ RAM."""
    item = rule_engine.get_glossary_term(term)
    if not item:
        raise HTTPException(status_code=404, detail=f"Thuật ngữ '{term}' không tồn tại.")
    return item.model_dump()


@router.post("/glossary", status_code=201)
async def create_glossary_term(
    request: GlossaryCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Thêm một thuật ngữ mới vào CSDL & reload RAM regex."""
    clean_term = request.term.strip()
    if not clean_term:
        raise HTTPException(status_code=400, detail="Thuật ngữ không được để trống.")

    # Check existence
    existing = await db.scalar(
        select(GlossaryTermModel).where(func.upper(GlossaryTermModel.term) == clean_term.upper())
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Thuật ngữ '{clean_term}' đã tồn tại trong CSDL.")

    model = GlossaryTermModel(
        term=clean_term,
        standard_case=(request.standard_case or clean_term).strip(),
        full_name_vi=request.full_name_vi.strip(),
        full_name_en=request.full_name_en.strip(),
        domain=request.domain.strip() or "General",
        incorrect_variants=request.incorrect_variants,
        synonyms=request.synonyms,
        do_not_translate=request.do_not_translate,
        description=request.description.strip(),
        is_active=True,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    # Hot-reload in memory
    rule_engine.reload()

    return {
        "message": f"Đã thêm thuật ngữ '{model.term}' thành công vào CSDL.",
        "item": {
            "term": model.term,
            "standard_case": model.standard_case,
            "full_name_vi": model.full_name_vi,
            "full_name_en": model.full_name_en,
            "domain": model.domain,
            "incorrect_variants": model.incorrect_variants,
            "synonyms": model.synonyms,
            "do_not_translate": model.do_not_translate,
            "description": model.description,
        },
    }


@router.put("/glossary/{term}")
async def update_glossary_term(
    term: str,
    request: GlossaryUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật một thuật ngữ đã có trong CSDL & reload RAM regex."""
    clean_term = term.strip().upper()
    model = await db.scalar(
        select(GlossaryTermModel).where(func.upper(GlossaryTermModel.term) == clean_term)
    )
    if not model:
        raise HTTPException(status_code=404, detail=f"Thuật ngữ '{term}' không tồn tại trong CSDL.")

    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Không có trường nào cần cập nhật.")

    for field, val in updates.items():
        if hasattr(model, field):
            setattr(model, field, val)

    await db.commit()
    await db.refresh(model)

    # Hot-reload in memory
    rule_engine.reload()

    return {
        "message": f"Đã cập nhật thuật ngữ '{model.term}' thành công trong CSDL.",
        "item": {
            "term": model.term,
            "standard_case": model.standard_case,
            "full_name_vi": model.full_name_vi,
            "full_name_en": model.full_name_en,
            "domain": model.domain,
            "incorrect_variants": model.incorrect_variants,
            "synonyms": model.synonyms,
            "do_not_translate": model.do_not_translate,
            "description": model.description,
        },
    }


@router.delete("/glossary/{term}")
async def delete_glossary_term(
    term: str,
    db: AsyncSession = Depends(get_db),
):
    """Xóa một thuật ngữ khỏi CSDL & reload RAM regex."""
    clean_term = term.strip().upper()
    model = await db.scalar(
        select(GlossaryTermModel).where(func.upper(GlossaryTermModel.term) == clean_term)
    )
    if not model:
        raise HTTPException(status_code=404, detail=f"Thuật ngữ '{term}' không tồn tại trong CSDL.")

    await db.delete(model)
    await db.commit()

    # Hot-reload in memory
    rule_engine.reload()

    return {"message": f"Đã xóa thuật ngữ '{term}' khỏi CSDL thành công."}


@router.post("/reload")
async def reload_rules():
    """Hot-reload: Nạp lại toàn bộ dữ liệu từ CSDL vào RAM mà không cần restart server."""
    result = rule_engine.reload()
    return {
        "message": "Đã nạp lại Rule Engine từ Database thành công.",
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
