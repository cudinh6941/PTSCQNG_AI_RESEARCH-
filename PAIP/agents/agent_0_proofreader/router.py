"""
Agent 0 — API Router.

Endpoints:
    POST /api/v1/proofread/text   — Kiểm tra text trực tiếp (JSON body)
    POST /api/v1/proofread/file   — Upload file Word/PDF/Text để kiểm tra (Multipart form)
"""

from fastapi import APIRouter, File, Form, UploadFile

from core.common.schemas import LLMProvider

import json
from fastapi.responses import StreamingResponse
import urllib.parse
from core.document.writer import document_writer

from .schemas import ExportDocxRequest, ProofreadRequest, ProofreadResponse
from .service import proofreader_service

router = APIRouter(prefix="/api/v1/proofread", tags=["Agent 0 — Document Proofreader"])


@router.post("/export-docx-inplace")
async def export_docx_inplace(
    file: UploadFile = File(..., description="File Word (.docx) gốc ban đầu"),
    replacements: str = Form(default="[]", description="JSON string của danh sách replacements [{'original': '...', 'suggested': '...'}]"),
    highlight_changes: bool = Form(default=False, description="Có tô màu vàng các từ đã sửa hay không"),
):
    """
    Sửa trực tiếp trên file Word (.docx) gốc và BẢO TOÀN 100% TOÀN BỘ ĐỊNH DẠNG:
    - Bảng biểu, cột, viền ô, màu sắc.
    - Header, footer, logo công ty, hình ảnh, chữ ký, watermark.
    - Font chữ, font size, bold/italic, căn lề.
    """
    content = await file.read()
    
    try:
        replacements_list = json.loads(replacements)
    except Exception:
        replacements_list = []

    docx_stream = document_writer.replace_in_docx(
        doc_bytes=content,
        replacements=replacements_list,
        highlight_changes=highlight_changes,
    )

    orig_name = file.filename or "tai_lieu.docx"
    base_name = orig_name.rsplit(".", 1)[0]
    out_filename = f"{base_name}_da_chinh_sua.docx"
    encoded_filename = urllib.parse.quote(out_filename)

    return StreamingResponse(
        docx_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post("/export-docx")
async def export_docx(
    request: ExportDocxRequest,
):
    """
    Xuất nội dung văn bản thành file Word (.docx) chuẩn định dạng hành chính.
    """
    docx_stream = document_writer.create_docx(
        text=request.text,
        title=request.title,
    )
    
    filename = request.filename.strip()
    if not filename.endswith(".docx"):
        filename = f"{filename}.docx"
    
    # URL encode filename for Content-Disposition header
    encoded_filename = urllib.parse.quote(filename)

    return StreamingResponse(
        docx_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )



@router.post("/text", response_model=ProofreadResponse)
async def proofread_text(
    request: ProofreadRequest,
) -> ProofreadResponse:
    """
    Kiểm tra chính tả cho đoạn text (nhận JSON body).
    """
    return await proofreader_service.proofread_text(
        text=request.document_text,
        mode=request.mode,
        custom_instructions=request.custom_instructions,
        provider=request.provider,
        model=request.model,
        user_id=request.user_id,
        department=request.department,
    )


@router.post("/file", response_model=ProofreadResponse)
async def proofread_file(
    file: UploadFile = File(..., description="File Word (.docx), PDF (.pdf), hoặc Text (.txt, .md)"),
    mode: str = Form(default="standard", description="Chế độ kiểm tra: standard | formal | strict"),
    custom_instructions: str | None = Form(default=None, description="Ghi chú thêm cho AI"),
    provider: LLMProvider | None = Form(default=None, description="LLM provider: openai/gemini/claude"),
    model: str | None = Form(default=None, description="Model cụ thể"),
    user_id: str | None = Form(default=None, description="ID người dùng"),
    department: str | None = Form(default=None, description="Phòng ban"),
) -> ProofreadResponse:
    """
    Kiểm tra chính tả cho file văn bản.

    Upload file Word (.docx), PDF (.pdf), hoặc Text (.txt/.md).
    """
    content = await file.read()

    return await proofreader_service.proofread_file(
        file_content=content,
        filename=file.filename or "unknown.txt",
        mode=mode,
        custom_instructions=custom_instructions,
        provider=provider,
        model=model,
        user_id=user_id,
        department=department,
    )


