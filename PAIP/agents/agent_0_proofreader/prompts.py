"""
Agent 0 — Prompts.

Prompt được thiết kế trong Obsidian:
    PTSC_AI_RnD/Lab&Research/Prompts/Prompt_Document_Proofread.md
Rồi đưa vào code ở đây.
"""

SYSTEM_PROMPT = """Bạn là chuyên gia rà soát văn bản tiếng Việt cấp cao dành cho doanh nghiệp, chuyên về:
1. Chính tả tiếng Việt: dấu thanh (hỏi/ngã), phụ âm (s/x, tr/ch, d/r/gi, l/n), nguyên âm và lỗi gõ phím.
2. Ngữ pháp & Cấu trúc câu: câu thiếu chủ vị, dấu câu ngắt dòng không hợp lý, câu văn rời rạc.
3. Cách dùng từ & Văn phong hành chính doanh nghiệp: chuẩn mực theo thể thức văn bản hành chính Việt Nam.

QUY TẮC BẤT BIẾN:
- TỰ ĐỘNG THÍCH ỨNG NGỮ CẢNH: Tự nhận diện bối cảnh tài liệu (Hợp đồng thương mại, Báo cáo kỹ thuật dầu khí, Tờ trình hành chính hay Thông báo nội bộ).
- TÔN TRỌNG THUẬT NGỮ CHUYÊN NGÀNH: Tuyệt đối giữ nguyên các thuật ngữ kỹ thuật, tên dự án, mã hiệu thiết bị, đơn vị đo lường, từ viết tắt (ví dụ: PTSC, EPC, HSE, CAPEX, P&ID, Lô B...).
- KHÔNG BÁO LỖI PHONG CÁCH CÁ NHÂN: Chỉ báo lỗi thật sự khi có căn cứ ngôn ngữ hoặc quy chuẩn hành chính.
- Trả lời 100% bằng tiếng Việt."""


def build_user_prompt(
    document_text: str,
    mode: str = "standard",
    custom_instructions: str | None = None,
) -> str:
    """Xây dựng user prompt động dựa trên chế độ kiểm tra và ghi chú người dùng."""
    
    mode_instructions = {
        "standard": (
            "CHẾ ĐỘ TIÊU CHUẨN: Tập trung bắt chính xác các lỗi chính tả, dấu thanh, phụ âm, nguyên âm và dấu câu."
        ),
        "formal": (
            "CHẾ ĐỘ TRANG TRỌNG / CÔNG VĂN: Soi kỹ văn phong hành chính theo Nghị định 30/2020/NĐ-CP, "
            "nâng cấp các từ ngữ suồng sã/khẩu ngữ thành từ ngữ trang trọng, lịch sự, chuẩn mực."
        ),
        "strict": (
            "CHẾ ĐỘ PHÁP LÝ & SỐ LIỆU CHẶT CHẼ: Soi kỹ tính chặt chẽ của các điều khoản, đối chiếu số tiền bằng số "
            "với số tiền bằng chữ, kiểm tra tính nhất quán của ngày tháng, danh xưng các bên và chế tài ràng buộc."
        ),
    }

    selected_mode_text = mode_instructions.get(mode, mode_instructions["standard"])
    
    custom_section = ""
    if custom_instructions and custom_instructions.strip():
        custom_section = f"\nYÊU CẦU ĐẶC BIỆT TỪ NGƯỜI DÙNG:\n> {custom_instructions.strip()}\n"

    return f"""{selected_mode_text}
{custom_section}
Hãy rà soát kỹ lưỡng văn bản dưới đây và trả về kết quả theo ĐÚNG định dạng JSON:

```json
{{
  "total_errors": <số lỗi phát hiện>,
  "errors": [
    {{
      "type": "<spelling|grammar|word_choice|punctuation>",
      "original": "<đoạn text gốc có lỗi>",
      "suggested": "<gợi ý sửa chính xác>",
      "explanation": "<giải thích ngắn gọn lý do>",
      "severity": "<low|medium|high>"
    }}
  ],
  "summary": "<tóm tắt ngắn gọn 1-2 câu về chất lượng văn bản và nhận xét chính>",
  "score": <điểm chất lượng từ 1.0 đến 10.0>
}}
```

VĂN BẢN CẦN KIỂM TRA:
---
{document_text}
---

Trả về duy nhất khối JSON hợp lệ, không thêm bất kỳ lời dẫn nào khác."""

