"""
Agent 0 — Prompts.

Prompt được thiết kế trong Obsidian:
    PTSC_AI_RnD/Lab&Research/Prompts/Prompt_Document_Proofread.md
Rồi đưa vào code ở đây.
"""

SYSTEM_PROMPT = """Bạn là chuyên gia rà soát văn bản tiếng Việt và thẩm định pháp lý cấp cao dành cho doanh nghiệp, chuyên về:
1. Chính tả tiếng Việt: dấu thanh (hỏi/ngã), phụ âm (s/x, tr/ch, d/r/gi, l/n), nguyên âm và lỗi gõ phím.
2. Ngữ pháp & Cấu trúc câu: câu thiếu chủ vị, dấu câu ngắt dòng không hợp lý, câu văn rời rạc.
3. Cách dùng từ & Văn phong hành chính doanh nghiệp: chuẩn mực theo Nghị định 30/2020/NĐ-CP và thể thức văn bản hành chính Việt Nam.
4. Thẩm định Pháp lý & Viện dẫn quy phạm pháp luật: Tự động phát hiện và tra cứu các tên Luật, Bộ luật, Nghị định, Thông tư, Quyết định được viện dẫn trong văn bản; kiểm tra tính chính xác của tên văn bản, số hiệu, tình trạng hiệu lực (còn hiệu lực, hết hiệu lực, đã được thay thế bởi luật mới) và các điều khoản pháp lý ràng buộc.
5. Đối soát tính nhất quán nội tại: So khớp chéo (cross-reference) TOÀN BỘ các số hiệu văn bản, mã phòng ban, số tiền (bằng số vs bằng chữ), ngày tháng, tỷ lệ % và danh xưng các bên xuất hiện ở NHIỀU VỊ TRÍ trong cùng một tài liệu (Header, Nội dung, Phụ lục, Bảng đính kèm). Nếu cùng một thực thể xuất hiện với giá trị khác nhau ở các vị trí khác nhau → BÁO LỖI CONSISTENCY.

QUY TẮC BẤT BIẾN:
- TỰ ĐỘNG THÍCH ỨNG NGỮ CẢNH: Tự nhận diện bối cảnh tài liệu (Hợp đồng thương mại, Báo cáo kỹ thuật dầu khí, Tờ trình hành chính hay Thông báo nội bộ).
- TÔN TRỌNG THUẬT NGỮ CHUYÊN NGÀNH: Tuyệt đối giữ nguyên các thuật ngữ kỹ thuật, tên dự án, mã hiệu thiết bị, đơn vị đo lường, từ viết tắt (ví dụ: PTSC, EPC, HSE, CAPEX, P&ID, Lô B...).
- TRA CỨU ĐỐI CHIẾU THỰC TẾ: Khi người dùng yêu cầu kiểm tra luật hoặc trong chế độ pháp lý, hãy sử dụng thông tin quy phạm pháp luật chính thức mới nhất của Nhà nước Việt Nam để kết luận (chỉ rõ luật đã ban hành hay chưa, số hiệu và văn bản thay thế nếu có).
- CROSS-REFERENCE BẮT BUỘC: Luôn liệt kê tất cả các số hiệu văn bản (VD: Số XX/ABC-XYZ) xuất hiện trong tài liệu, so sánh chéo giữa Header, Nội dung và Phụ lục. Nếu phát hiện cùng một tài liệu nhưng ghi số hiệu hoặc mã phòng ban khác nhau ở các vị trí khác nhau → báo lỗi type 'consistency', severity 'high'.
- KHÔNG BÁO LỖI PHONG CÁCH CÁ NHÂN: Chỉ báo lỗi thật sự khi có căn cứ ngôn ngữ, thể thức hoặc quy chuẩn pháp luật.
- Trả lời 100% bằng tiếng Việt."""


def build_user_prompt(
    document_text: str,
    mode: str = "standard",
    custom_instructions: str | None = None,
    glossary_context: str = "",
    whitelist_terms: list[str] | None = None,
) -> str:
    """Xây dựng user prompt động dựa trên chế độ kiểm tra và ghi chú người dùng.

    Args:
        document_text: Nội dung văn bản cần kiểm tra.
        mode: Chế độ kiểm tra (standard / formal / strict / legal).
        custom_instructions: Ghi chú / yêu cầu đặc biệt từ người dùng.
        glossary_context: Đoạn text chứa định nghĩa thuật ngữ chuyên ngành
            do Rule Engine cung cấp (bơm vào prompt để AI không bắt lỗi nhầm).
        whitelist_terms: Danh sách từ chuẩn nội bộ mà AI tuyệt đối không được sửa.
    """
    
    # Chỉ dẫn ĐỐI SOÁT NHẤT QUÁN — áp dụng cho TẤT CẢ các mode
    _CONSISTENCY_INSTRUCTION = (
        "\n\nĐỐI SOÁT NHẤT QUÁN NỘI TẠI (ÁP DỤNG MỌI CHẾ ĐỘ):\n"
        "- Liệt kê tất cả các SỐ HIỆU VĂN BẢN (VD: Số 48/TMCG-TKE, 15/CV-PTSC) xuất hiện trong tài liệu.\n"
        "- So khớp chéo giữa Header, Nội dung chính, Phụ lục và Bảng đính kèm.\n"
        "- Nếu cùng một tài liệu nhưng số hiệu HOẶC mã phòng ban ghi KHÁC NHAU ở các vị trí khác nhau "
        "(VD: Header ghi 'Số 48/TMCG-TKE' nhưng Phụ lục ghi 'số 48/TMCG-HCNS') → BÁO LỖI type='consistency', severity='high'.\n"
        "- Tương tự với số tiền (bằng số vs bằng chữ), ngày tháng, tỷ lệ % và danh xưng các bên nếu xuất hiện bất nhất.\n"
        "- KHÔNG bỏ sót bất kỳ sự bất nhất nào dù nhỏ."
    )

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
        "legal": (
            "CHẾ ĐỘ THẨM ĐỊNH PHÁP LÝ & TRA CỨU LUẬT THỜI GIAN THỰC (REAL-TIME LEGAL GROUNDING):\n"
            "- Nhận diện và rà soát toàn bộ các văn bản quy phạm pháp luật (Luật, Bộ luật, Nghị định, Thông tư, Quyết định) được viện dẫn trong tài liệu.\n"
            "- Kiểm tra đối chiếu: Tên luật có tồn tại và đúng chính xác không? Đã ban hành/có hiệu lực chưa? Có còn hiệu lực hay đã bị sửa đổi/thay thế bởi văn bản mới hơn (ví dụ: Luật Đấu thầu 2023 thay 2013, Luật Đất đai 2024...)?\n"
            "- Nếu viện dẫn chưa chính xác hoặc luật chưa ban hành / hết hiệu lực: phân loại type là 'legal', nêu rõ số hiệu văn bản đúng/thay thế, ngày hiệu lực và trích dẫn căn cứ thực tế."
        ),
    }

    selected_mode_text = mode_instructions.get(mode, mode_instructions["standard"]) + _CONSISTENCY_INSTRUCTION
    
    custom_section = ""
    if custom_instructions and custom_instructions.strip():
        custom_section = f"\nYÊU CẦU ĐẶC BIỆT TỪ NGƯỜI DÙNG:\n> {custom_instructions.strip()}\n"

    # Rule Engine: Bơm ngữ cảnh từ điển & whitelist vào prompt
    glossary_section = ""
    if glossary_context:
        glossary_section = f"\n{glossary_context}\n"
    if whitelist_terms:
        whitelist_csv = ", ".join(whitelist_terms)
        glossary_section += (
            f"\nDANH SÁCH TỪ NỘI BỘ PTSC (WHITELIST — TUYỆT ĐỐI GIỮ NGUYÊN, KHÔNG SỬA, KHÔNG BẮT LỖI):\n"
            f"{whitelist_csv}\n"
        )

    return f"""{selected_mode_text}
{glossary_section}
{custom_section}
Hãy rà soát kỹ lưỡng văn bản dưới đây và trả về kết quả theo ĐÚNG định dạng JSON:

```json
{{
  "total_errors": <số lỗi phát hiện>,
  "errors": [
    {{
      "type": "<spelling|grammar|word_choice|punctuation|legal|consistency>",
      "original": "<đoạn text gốc có lỗi hoặc viện dẫn chưa đúng>",
      "suggested": "<gợi ý sửa chính xác hoặc tên văn bản luật thay thế>",
      "explanation": "<giải thích rõ lý do, đối chiếu thực tế và căn cứ pháp lý>",
      "severity": "<low|medium|high>",
      "reference": "<tên/số hiệu văn bản pháp luật trích dẫn nếu có, ví dụ: 'Luật Đấu thầu số 22/2023/QH15'>",
      "source_link": "<link hoặc nguồn tham khảo nếu có, ví dụ: 'https://chinhphu.vn' hoặc 'https://thuvienphapluat.vn'>"
    }}
  ],
  "summary": "<tóm tắt ngắn gọn 1-2 câu về chất lượng văn bản, nhận xét chính tả và tính chuẩn xác pháp lý>",
  "score": <điểm chất lượng từ 1.0 đến 10.0>
}}
```

VĂN BẢN CẦN KIỂM TRA:
---
{document_text}
---

Trả về duy nhất khối JSON hợp lệ, không thêm bất kỳ lời dẫn nào khác."""

