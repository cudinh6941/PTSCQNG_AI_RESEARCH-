"""
PAIP — Document Format & Layout Inspection Router (Nghị định 30/2020/NĐ-CP).

Endpoints:
    POST /api/v1/format/inspect      — Kiểm tra và báo cáo vi phạm lề, font, căn dòng của file Word
    POST /api/v1/format/auto-format  — Tự động chuẩn hóa file Word theo Nghị định 30 (1-Click)
"""

import urllib.parse
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from core.document.format_inspector import docx_format_inspector, docx_auto_formatter

router = APIRouter(prefix="/api/v1/format", tags=["Format & Layout Inspector (NĐ 30)"])


@router.post("/inspect")
async def inspect_docx_format(
    file: UploadFile = File(..., description="File Word (.docx) cần kiểm tra thể thức"),
):
    """
    Kiểm tra căn lề, font chữ, căn đoạn (Justify) theo quy định Nghị định 30/2020/NĐ-CP.
    """
    if not file.filename.lower().endswith(".docx"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Chỉ hỗ trợ kiểm tra thể thức cho định dạng file Word (.docx)"}
        )

    content = await file.read()
    report = docx_format_inspector.inspect(content)
    return report


@router.post("/auto-format")
async def auto_format_docx(
    file: UploadFile = File(..., description="File Word (.docx) cần tự động chuẩn hóa"),
):
    """
    Tự động chuẩn hóa 1-Click toàn bộ file Word (.docx):
    - Khổ giấy chuẩn A4
    - Lề: Trái 3.0cm, Phải 1.5cm, Trên 2.0cm, Dưới 2.0cm
    - Toàn bộ font về Times New Roman
    - Căn đều Justified các đoạn văn
    - Giãn dòng chuẩn 1.15 lines
    """
    if not file.filename.lower().endswith(".docx"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Chỉ hỗ trợ tự động chuẩn hóa cho định dạng file Word (.docx)"}
        )

    content = await file.read()
    formatted_stream = docx_auto_formatter.auto_format(content)

    orig_name = file.filename or "tai_lieu.docx"
    base_name = orig_name.rsplit(".", 1)[0]
    out_filename = f"{base_name}_ChuanHoa_TheThuc_ND30.docx"
    encoded_filename = urllib.parse.quote(out_filename)

    return StreamingResponse(
        formatted_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
