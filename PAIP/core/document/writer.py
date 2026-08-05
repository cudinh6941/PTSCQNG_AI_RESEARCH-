"""
PAIP Document Writer — Xuất văn bản thành file Word (.docx) chuẩn định dạng.

Hỗ trợ 2 chế độ:
1. In-Place Word Replacement: Nhận file Word gốc (.docx) và danh sách lỗi đã sửa,
   thay thế trực tiếp trong cấu trúc tài liệu gốc và BẢO TOÀN 100% định dạng (Bảng biểu,
   Header, Footer, Logo, Màu sắc, Font chữ, Căn lề, Section).
2. New Document Generation: Tạo file Word mới chuẩn Nghị định 30/2020/NĐ-CP từ văn bản thuần.
"""

from io import BytesIO
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX

from core.common.logger import logger


class DocumentWriter:
    """Tạo và xuất tài liệu Word (.docx) từ nội dung văn bản."""

    # ── Chế độ 1: Thay thế In-Place trên File Word Gốc (Giữ 100% Format) ───

    @staticmethod
    def replace_in_docx(
        doc_bytes: bytes,
        replacements: list[dict],
        highlight_changes: bool = False,
    ) -> BytesIO:
        """
        Sửa trực tiếp trên file Word gốc (.docx).

        Args:
            doc_bytes: Binary của file Word gốc được tải lên
            replacements: Danh sách dict [{'original': '...', 'suggested': '...'}]
            highlight_changes: Nếu True, bôi vàng các từ đã được sửa để dễ kiểm tra

        Returns:
            BytesIO stream chứa file Word hoàn chỉnh giữ nguyên 100% template và format gốc
        """
        doc = Document(BytesIO(doc_bytes))

        # Chuẩn hóa danh sách thay thế hợp lệ (bỏ qua rỗng hoặc giống nhau)
        valid_replacements = []
        for item in replacements:
            orig = item.get("original", "").strip()
            sugg = item.get("suggested", "").strip()
            if orig and sugg and orig != sugg:
                valid_replacements.append((orig, sugg))

        if not valid_replacements:
            logger.info("No valid replacements to apply to original docx")
            stream = BytesIO(doc_bytes)
            stream.seek(0)
            return stream

        def process_paragraph(p):
            for orig, sugg in valid_replacements:
                DocumentWriter._replace_text_in_paragraph(p, orig, sugg, highlight=highlight_changes)

        # 1. Quét Paragraphs trong thân tài liệu
        for p in doc.paragraphs:
            process_paragraph(p)

        # 2. Quét Paragraphs trong tất cả các Bảng Biểu (Tables)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        process_paragraph(p)

        # 3. Quét Header & Footer trong tất cả các Section
        for section in doc.sections:
            for p in section.header.paragraphs:
                process_paragraph(p)
            for table in section.header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            process_paragraph(p)

            for p in section.footer.paragraphs:
                process_paragraph(p)
            for table in section.footer.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            process_paragraph(p)

        stream = BytesIO()
        doc.save(stream)
        stream.seek(0)
        logger.info(f"Successfully applied {len(valid_replacements)} in-place replacements to Word document")
        return stream

    @staticmethod
    def _replace_text_in_paragraph(
        paragraph,
        search_text: str,
        replace_text: str,
        highlight: bool = False,
    ) -> bool:
        """
        Thay thế chuỗi văn bản trong một đoạn văn (Paragraph) bảo toàn 100% định dạng (Runs).
        Bảo vệ tuyệt đối font chữ, cỡ chữ, in đậm, in nghiêng, màu sắc của các Run trước và sau.
        """
        if not search_text or not paragraph.runs:
            return False

        replaced_any = False
        find_from = 0

        while True:
            # Tái tạo full_text từ các runs hiện hành
            full_text = "".join(run.text for run in paragraph.runs)
            start_idx = full_text.find(search_text, find_from)
            if start_idx == -1:
                break

            end_idx = start_idx + len(search_text)
            replaced_any = True

            # Xác định chính xác các Run giao thoa với khoảng [start_idx, end_idx)
            curr_char = 0
            start_run_idx = None
            start_run_offset = None
            end_run_idx = None
            end_run_offset = None

            for i, run in enumerate(paragraph.runs):
                run_len = len(run.text)
                run_start = curr_char
                run_end = curr_char + run_len

                # Run chứa ký tự bắt đầu của search_text
                if start_run_idx is None and run_start <= start_idx < run_end:
                    start_run_idx = i
                    start_run_offset = start_idx - run_start

                # Run chứa ký tự kết thúc của search_text (end_idx - 1)
                if end_run_idx is None and run_start <= (end_idx - 1) < run_end:
                    end_run_idx = i
                    end_run_offset = end_idx - run_start

                curr_char = run_end

            # Nếu không định vị được run (trường hợp biên an toàn), thoát vòng lặp
            if start_run_idx is None or end_run_idx is None:
                break

            start_run = paragraph.runs[start_run_idx]
            end_run = paragraph.runs[end_run_idx]

            if start_run_idx == end_run_idx:
                # Trường hợp 1: Từ cần sửa nằm trọn vẹn trong 1 Run duy nhất
                orig_text = start_run.text
                start_run.text = orig_text[:start_run_offset] + replace_text + orig_text[end_run_offset:]
                if highlight:
                    start_run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            else:
                # Trường hợp 2: Từ cần sửa bị chia cắt qua nhiều Runs
                # 1. start_run: Giữ lại phần text trước start_idx và ghép replace_text
                orig_start_text = start_run.text
                start_run.text = orig_start_text[:start_run_offset] + replace_text
                if highlight:
                    start_run.font.highlight_color = WD_COLOR_INDEX.YELLOW

                # 2. Các Run trung gian nằm giữa start_run và end_run: Xóa nội dung trùng khớp
                for mid_idx in range(start_run_idx + 1, end_run_idx):
                    paragraph.runs[mid_idx].text = ""

                # 3. end_run: Giữ lại phần text phía sau end_idx
                orig_end_text = end_run.text
                end_run.text = orig_end_text[end_run_offset:]

            # Dịch chuyển vị trí tìm kiếm tiếp theo ra sau đoạn text vừa được thay thế
            find_from = start_idx + len(replace_text)

        return replaced_any

    # ── Chế độ 2: Tạo File Word Mới Chuẩn Thể Thức (New Document) ──────────

    @staticmethod
    def create_docx(
        text: str,
        title: str | None = None,
        font_name: str = "Times New Roman",
        font_size_pt: int = 13,
    ) -> BytesIO:
        """
        Tạo file Word .docx từ văn bản thuần theo quy chuẩn NĐ 30/2020/NĐ-CP.
        """
        doc = Document()

        # Căn lề chuẩn NĐ 30: Trên 2cm, Dưới 2cm, Trái 3cm (1.18in), Phải 1.5cm (0.59in)
        for section in doc.sections:
            section.top_margin = Inches(0.79)     # 20mm
            section.bottom_margin = Inches(0.79)  # 20mm
            section.left_margin = Inches(1.18)    # 30mm
            section.right_margin = Inches(0.59)   # 15mm

        # Cài đặt style Normal
        normal_style = doc.styles["Normal"]
        font = normal_style.font
        font.name = font_name
        font.size = Pt(font_size_pt)
        font.color.rgb = RGBColor(17, 24, 39)

        # Tiêu đề tài liệu nếu có
        if title:
            title_p = doc.add_paragraph()
            title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title_p.paragraph_format.space_before = Pt(0)
            title_p.paragraph_format.space_after = Pt(12)
            title_run = title_p.add_run(title.upper())
            title_run.bold = True
            title_run.font.size = Pt(font_size_pt + 3)

        # Phân tách văn bản thành các đoạn
        lines = text.split("\n")
        
        i = 0
        while i < len(lines):
            raw_line = lines[i]
            trimmed = raw_line.strip()

            # Bỏ qua dòng trống liên tiếp nhưng giữ 1 khoảng cách nhẹ
            if not trimmed:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.line_spacing = 1.15
                i += 1
                continue

            # Xử lý Tiêu đề Heading
            if trimmed.startswith("# "):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
                run = p.add_run(trimmed[2:])
                run.bold = True
                run.font.size = Pt(font_size_pt + 2)
            elif trimmed.startswith("## "):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(4)
                run = p.add_run(trimmed[3:])
                run.bold = True
                run.font.size = Pt(font_size_pt + 1)
            elif trimmed.startswith("### "):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run(trimmed[4:])
                run.bold = True
                run.font.size = Pt(font_size_pt)
            
            # Xử lý Danh sách gạch đầu dòng / số thứ tự
            elif trimmed.startswith("- ") or trimmed.startswith("* ") or trimmed.startswith("• "):
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(3)
                p.add_run(trimmed[2:])
            elif re.match(r"^\d+[\.\)]\s+", trimmed):
                p = doc.add_paragraph(style="List Number")
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(3)
                p.add_run(re.sub(r"^\d+[\.\)]\s+", "", trimmed))

            # Đoạn văn bản thông thường
            else:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.15
                p.paragraph_format.space_after = Pt(4)
                
                # Căn giữa cho Quốc hiệu tiêu ngữ
                if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in trimmed or "Độc lập - Tự do - Hạnh phúc" in trimmed:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run(trimmed)
                    run.bold = True
                elif trimmed.startswith("Kính gửi:") or trimmed.startswith("Kính gởi:"):
                    run = p.add_run(trimmed)
                    run.bold = True
                elif trimmed.startswith("Điều ") or trimmed.startswith("ĐIỀU "):
                    run = p.add_run(trimmed)
                    run.bold = True
                else:
                    p.add_run(trimmed)

            i += 1

        stream = BytesIO()
        doc.save(stream)
        stream.seek(0)
        logger.info(f"Generated clean Word document ({len(text)} characters)")
        return stream


document_writer = DocumentWriter()
