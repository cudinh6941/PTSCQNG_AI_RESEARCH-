"""
PAIP Document Format Inspector & Auto-Formatter.

Kiểm tra và tự động chuẩn hóa định dạng văn bản Word (.docx) theo:
- Nghị định 30/2020/NĐ-CP về công tác văn thư
- Quy định thể thức & mẫu văn bản nội bộ Tổng công ty PTSC
"""

from io import BytesIO
import re
import zipfile
import xml.etree.ElementTree as ET
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.oxml.ns import qn

from core.common.logger import logger


def _extract_theme_fonts(doc_bytes: bytes) -> dict[str, str]:
    """
    Trích xuất bảng font chủ đề (Office Theme Fonts) từ word/theme/theme1.xml.
    Mặc định của Microsoft Word là: Minor=Calibri, Major=Calibri Light.
    """
    theme_fonts = {"minor": "Calibri", "major": "Calibri Light"}
    try:
        with zipfile.ZipFile(BytesIO(doc_bytes), "r") as z:
            if "word/theme/theme1.xml" in z.namelist():
                theme_xml = z.read("word/theme/theme1.xml")
                root = ET.fromstring(theme_xml)
                ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                fontScheme = root.find(".//a:fontScheme", ns)
                if fontScheme is not None:
                    major = fontScheme.find("a:majorFont/a:latin", ns)
                    minor = fontScheme.find("a:minorFont/a:latin", ns)
                    if major is not None and "typeface" in major.attrib and major.attrib["typeface"]:
                        theme_fonts["major"] = major.attrib["typeface"]
                    if minor is not None and "typeface" in minor.attrib and minor.attrib["typeface"]:
                        theme_fonts["minor"] = minor.attrib["typeface"]
    except Exception as e:
        logger.debug(f"Could not extract theme fonts: {e}")
    return theme_fonts


def _resolve_run_font(run, paragraph, theme_fonts: dict[str, str], style_cache: dict[str, str]) -> str:
    """
    Phân giải chính xác font chữ đang hiển thị của một Run qua đầy đủ các tầng:
    1. Direct Run Font (w:ascii, w:hAnsi, w:cs, w:eastAsia)
    2. Theme Font (w:asciiTheme, w:hAnsiTheme -> minor=Calibri, major=Calibri Light)
    3. Paragraph Style (kế thừa từ Style cha)
    4. Mặc định tài liệu
    """
    # 1. Trực tiếp từ thuộc tính python-docx
    if run.font and run.font.name:
        return run.font.name

    # 2. Quét tầng OpenXML Run Properties (rPr)
    if hasattr(run, '_r') and run._r is not None:
        rPr = run._r.rPr
        if rPr is not None and rPr.rFonts is not None:
            rFonts = rPr.rFonts
            # 2.1 Font tên trực tiếp
            direct_font = (
                rFonts.get(qn('w:ascii'))
                or rFonts.get(qn('w:hAnsi'))
                or rFonts.get(qn('w:cs'))
                or rFonts.get(qn('w:eastAsia'))
            )
            if direct_font:
                return direct_font

            # 2.2 Theme font (Calibri / Calibri Light theo Theme Office)
            theme = (
                rFonts.get(qn('w:asciiTheme'))
                or rFonts.get(qn('w:hAnsiTheme'))
                or rFonts.get(qn('w:cstheme'))
                or rFonts.get(qn('w:eastAsiaTheme'))
            )
            if theme:
                theme_lower = theme.lower()
                if "minor" in theme_lower:
                    return theme_fonts.get("minor", "Calibri")
                elif "major" in theme_lower:
                    return theme_fonts.get("major", "Calibri Light")
                return theme

    # 3. Kế thừa từ Style của Paragraph (nếu có cache)
    style_name = paragraph.style.name if (paragraph and paragraph.style) else None
    if style_name:
        if style_name in style_cache:
            return style_cache[style_name]

        # Phân giải font của Style
        style_font = "Times New Roman"
        try:
            p_style = paragraph.style
            if hasattr(p_style, 'font') and p_style.font and p_style.font.name:
                style_font = p_style.font.name
            elif hasattr(p_style, '_element') and p_style._element is not None:
                s_rPr = p_style._element.rPr
                if s_rPr is not None and s_rPr.rFonts is not None:
                    s_fonts = s_rPr.rFonts
                    s_direct = s_fonts.get(qn('w:ascii')) or s_fonts.get(qn('w:hAnsi'))
                    if s_direct:
                        style_font = s_direct
                    else:
                        s_theme = s_fonts.get(qn('w:asciiTheme')) or s_fonts.get(qn('w:hAnsiTheme'))
                        if s_theme and "minor" in s_theme.lower():
                            style_font = theme_fonts.get("minor", "Calibri")
                        elif s_theme and "major" in s_theme.lower():
                            style_font = theme_fonts.get("major", "Calibri Light")
        except Exception:
            pass

        style_cache[style_name] = style_font
        return style_font

    return "Times New Roman"


def _force_times_new_roman(run) -> None:
    """Ghi đè triệt để font Times New Roman trên mọi thuộc tính OpenXML và xóa sạch Theme font."""
    run.font.name = "Times New Roman"
    if hasattr(run, '_r') and run._r is not None:
        rPr = run._r.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        # Đặt font chuẩn
        rFonts.set(qn('w:ascii'), 'Times New Roman')
        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
        rFonts.set(qn('w:cs'), 'Times New Roman')
        rFonts.set(qn('w:eastAsia'), 'Times New Roman')

        # Xóa triệt để các thuộc tính theme font để Word không bao giờ bị nhảy về Calibri
        for theme_attr in ('w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme'):
            attr_qn = qn(theme_attr)
            if attr_qn in rFonts.attrib:
                del rFonts.attrib[attr_qn]


class DocxFormatInspector:
    """Kiểm tra và báo cáo chi tiết vi phạm thể thức, căn lề, font chữ trên file Word (.docx)."""

    # Ngưỡng chuẩn theo Nghị định 30/2020/NĐ-CP
    MARGIN_STANDARDS = {
        "top": {"min_cm": 2.0, "max_cm": 2.5, "default_cm": 2.0},
        "bottom": {"min_cm": 2.0, "max_cm": 2.5, "default_cm": 2.0},
        "left": {"min_cm": 3.0, "max_cm": 3.5, "default_cm": 3.0},   # Chừa lề đóng gáy
        "right": {"min_cm": 1.5, "max_cm": 2.0, "default_cm": 1.5},
    }
    STANDARD_FONT = "Times New Roman"

    @classmethod
    def inspect(cls, doc_bytes: bytes) -> dict:
        """
        Quét chi tiết định dạng của file Word và trả về báo cáo vi phạm.
        Hỗ trợ duyệt qua cả Paragraphs, Bảng biểu (Tables), Headers/Footers và Theme Fonts.
        """
        try:
            doc = Document(BytesIO(doc_bytes))
        except Exception as e:
            logger.error(f"Failed to parse docx for format inspection: {e}")
            return {
                "success": False,
                "error": str(e),
                "margins": {"top_cm": 2.0, "bottom_cm": 2.0, "left_cm": 3.0, "right_cm": 1.5},
                "dominant_font": "Unknown",
                "font_clean": True,
                "font_issues": [],
                "alignment_clean": True,
                "alignment_issues": [],
                "total_paragraphs": 0,
            }

        # 0. Trích xuất bảng Theme Fonts
        theme_fonts = _extract_theme_fonts(doc_bytes)
        style_cache: dict[str, str] = {}

        # 1. Kiểm tra Căn Lề (Margins) trên Section đầu tiên
        section = doc.sections[0] if doc.sections else None
        if section:
            top_cm = round(section.top_margin.cm, 2)
            bottom_cm = round(section.bottom_margin.cm, 2)
            left_cm = round(section.left_margin.cm, 2)
            right_cm = round(section.right_margin.cm, 2)
        else:
            top_cm, bottom_cm, left_cm, right_cm = 2.0, 2.0, 3.0, 1.5

        top_valid = cls.MARGIN_STANDARDS["top"]["min_cm"] <= top_cm <= cls.MARGIN_STANDARDS["top"]["max_cm"]
        bottom_valid = cls.MARGIN_STANDARDS["bottom"]["min_cm"] <= bottom_cm <= cls.MARGIN_STANDARDS["bottom"]["max_cm"]
        left_valid = cls.MARGIN_STANDARDS["left"]["min_cm"] <= left_cm <= cls.MARGIN_STANDARDS["left"]["max_cm"]
        right_valid = cls.MARGIN_STANDARDS["right"]["min_cm"] <= right_cm <= cls.MARGIN_STANDARDS["right"]["max_cm"]
        margins_compliant = top_valid and bottom_valid and left_valid and right_valid

        # 2. Quét Font chữ và Căn lề đoạn văn toàn diện
        font_counts: dict[str, int] = {}
        font_issues: list[dict] = []
        alignment_issues: list[dict] = []
        total_elements = 0

        # Helper thu thập run
        def _scan_paragraph(p, location_label: str, check_align: bool = False):
            nonlocal total_elements
            text = p.text.strip()
            if not text:
                return

            total_elements += 1

            for r in p.runs:
                r_text = r.text.strip()
                if not r_text:
                    continue

                font_name = _resolve_run_font(r, p, theme_fonts, style_cache)
                font_counts[font_name] = font_counts.get(font_name, 0) + len(r_text)

                if font_name.lower() != cls.STANDARD_FONT.lower():
                    snippet = r_text if len(r_text) <= 60 else (r_text[:57] + "...")
                    if len(font_issues) < 15 and not any(i["snippet"] == snippet for i in font_issues):
                        font_issues.append({
                            "location": location_label,
                            "font": font_name,
                            "expected_font": cls.STANDARD_FONT,
                            "snippet": snippet,
                        })

            if check_align and len(text) > 80:
                if p.alignment in (WD_ALIGN_PARAGRAPH.LEFT, None):
                    if len(alignment_issues) < 10:
                        snippet = text if len(text) <= 65 else (text[:62] + "...")
                        alignment_issues.append({
                            "location": location_label,
                            "snippet": snippet,
                            "current_alignment": "LEFT",
                            "expected_alignment": "JUSTIFY"
                        })

        # 2.1 Quét Thân bài
        for i, p in enumerate(doc.paragraphs):
            _scan_paragraph(p, f"Đoạn văn {i+1}", check_align=True)

        # 2.2 Quét Bảng biểu (Tables)
        for t_idx, table in enumerate(doc.tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    for p in cell.paragraphs:
                        _scan_paragraph(p, f"Bảng {t_idx+1} (Hàng {r_idx+1}, Cột {c_idx+1})", check_align=False)

        # 2.3 Quét Header & Footer
        for s_idx, sec in enumerate(doc.sections):
            for p in sec.header.paragraphs:
                _scan_paragraph(p, f"Header trang (Section {s_idx+1})", check_align=False)
            for p in sec.footer.paragraphs:
                _scan_paragraph(p, f"Footer trang (Section {s_idx+1})", check_align=False)

        dominant_font = max(font_counts.keys(), key=font_counts.get) if font_counts else "Times New Roman"
        font_clean = (
            dominant_font.lower() == cls.STANDARD_FONT.lower()
            and len(font_issues) == 0
        )
        alignment_clean = len(alignment_issues) == 0

        return {
            "success": True,
            "margins": {
                "top_cm": top_cm,
                "bottom_cm": bottom_cm,
                "left_cm": left_cm,
                "right_cm": right_cm,
            },
            "margins_compliant": margins_compliant,
            "dominant_font": dominant_font,
            "font_clean": font_clean,
            "font_issues": font_issues,
            "alignment_clean": alignment_clean,
            "alignment_issues": alignment_issues,
            "total_paragraphs": total_elements,
        }


class DocxAutoFormatter:
    """Tự động chuẩn hóa toàn bộ file Word (.docx) theo Nghị định 30/2020/NĐ-CP."""

    @classmethod
    def auto_format(cls, doc_bytes: bytes) -> BytesIO:
        """
        Tự động:
        1. Đặt kích thước trang A4 (210mm x 297mm) cho mọi Section.
        2. Chuẩn hóa lề trang: Trái 3.0cm, Phải 1.5cm, Trên 2.0cm, Dưới 2.0cm.
        3. Chuẩn hóa triệt để toàn bộ Font về Times New Roman (Paragraphs, Bảng biểu, Header, Footer).
        4. Căn đều 2 bên (Justified) cho các đoạn văn thân bài (> 70 ký tự).
        5. Đặt giãn dòng chuẩn 1.15 lines và cách đoạn 3pt.
        """
        doc = Document(BytesIO(doc_bytes))

        # 1. Căn lề & Kích thước trang chuẩn A4 cho tất cả các Section
        for section in doc.sections:
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)
            section.left_margin = Cm(3.0)
            section.right_margin = Cm(1.5)
            section.top_margin = Cm(2.0)
            section.bottom_margin = Cm(2.0)

        # 2. Cập nhật Styles mặc định của tài liệu sang Times New Roman
        for style_name in ('Normal', 'Body Text', 'Body Text 2', 'Table Grid', 'No Spacing'):
            if style_name in doc.styles:
                try:
                    style = doc.styles[style_name]
                    style.font.name = 'Times New Roman'
                    if hasattr(style, '_element') and style._element is not None:
                        rPr = style._element.get_or_add_rPr()
                        rFonts = rPr.get_or_add_rFonts()
                        rFonts.set(qn('w:ascii'), 'Times New Roman')
                        rFonts.set(qn('w:hAnsi'), 'Times New Roman')
                        rFonts.set(qn('w:cs'), 'Times New Roman')
                        rFonts.set(qn('w:eastAsia'), 'Times New Roman')
                        for theme_attr in ('w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme'):
                            attr_qn = qn(theme_attr)
                            if attr_qn in rFonts.attrib:
                                del rFonts.attrib[attr_qn]
                except Exception:
                    pass

        # 3. Chuẩn hóa Paragraphs trong thân tài liệu
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            for r in p.runs:
                _force_times_new_roman(r)

            # Căn đều Justified cho các đoạn nội dung dài ngoài bảng
            if len(text) > 70 and p.alignment in (WD_ALIGN_PARAGRAPH.LEFT, None):
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            # Giãn dòng chuẩn
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(3)

        # 4. Chuẩn hóa Font trong toàn bộ Bảng biểu (Tables)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for r in p.runs:
                            _force_times_new_roman(r)

        # 5. Chuẩn hóa Header & Footer
        for section in doc.sections:
            for p in section.header.paragraphs:
                for r in p.runs:
                    _force_times_new_roman(r)
            for p in section.footer.paragraphs:
                for r in p.runs:
                    _force_times_new_roman(r)

        out_stream = BytesIO()
        doc.save(out_stream)
        out_stream.seek(0)
        logger.info("Successfully auto-formatted Word document according to Decree 30 / PTSC standard.")
        return out_stream


docx_format_inspector = DocxFormatInspector()
docx_auto_formatter = DocxAutoFormatter()

