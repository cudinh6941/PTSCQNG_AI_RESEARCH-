"""
Document Code Extractor — Bóc tách số hiệu công văn, hợp đồng, quyết định.
"""

from __future__ import annotations

import re
from typing import Any

from .base_extractor import BaseEntityExtractor, EntityType, ExtractedEntity


class DocumentCodeExtractor(BaseEntityExtractor):
    """
    Trích xuất số hiệu văn bản (Dispatch / Document / Contract Code).

    Ví dụ:
    - 43/TMCG-TKE
    - 01/2026/QĐ-PTSC
    - 15/HĐ-PTSC/2026
    - 123/TB-PTSC QNg
    """

    # Pattern bóc tách số hiệu văn bản chuẩn Việt Nam / PTSC
    _CODE_PATTERN = re.compile(
        r"(?:(?:Số|số|Hợp đồng số|HĐ số|Công văn số|Tờ trình số|Quyết định số|Thông báo số)[:\s]+)?"
        r"(\b\d{1,5}(?:[A-Za-z]|\/\d{4})?\s*\/\s*[A-ZĐa-zđ0-9\-_]+(?:\s*[\/\-]\s*[A-ZĐa-zđ0-9\-_]+)*\b)",
        re.IGNORECASE | re.UNICODE,
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.DOCUMENT_CODE

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text:
            return []

        results: list[ExtractedEntity] = []
        total_len = len(text)
        lines = text.split("\n")

        # Map character offsets to line numbers
        line_offsets: list[int] = []
        cur_offset = 0
        for l in lines:
            line_offsets.append(cur_offset)
            cur_offset += len(l) + 1

        def get_line_num(char_idx: int) -> int:
            for i, offset in enumerate(line_offsets):
                if offset > char_idx:
                    return i
            return len(lines)

        for match in self._CODE_PATTERN.finditer(text):
            raw_matched = match.group(1).strip()
            
            # Loại trừ trường hợp nhầm lẫn ngày tháng (ví dụ: 06/08/2026)
            if re.match(r"^\d{1,2}\/\d{1,2}\/\d{4}$", raw_matched):
                continue
            
            # Loại trừ tỉ lệ hoặc phép chia đơn thuần (ví dụ: 1/2)
            if re.match(r"^\d+\/\d+$", raw_matched):
                continue

            start_char, end_char = match.span(1)
            line_num = get_line_num(start_char)

            # Xác định section
            section = "body"
            prefix_context = text[max(0, start_char - 150):start_char].lower()
            if any(kw in prefix_context for kw in ("phụ lục", "đính kèm", "appendix", "bảng kê")):
                section = "attachment"
            elif start_char < total_len * 0.20 or (line_num <= 5 and total_len > 300):
                section = "header"

            # Trích xuất snippet
            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            # Chuẩn hóa mã số (bỏ khoảng trắng thừa quanh dấu gạch chéo)
            normalized_code = re.sub(r"\s*\/\s*", "/", raw_matched).strip().upper()

            # Phân tách số và suffix
            # VD: 43/TMCG-TKE -> num="43", suffix="TMCG-TKE"
            parts = normalized_code.split("/", 1)
            doc_number = parts[0]
            doc_suffix = parts[1] if len(parts) > 1 else ""

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.DOCUMENT_CODE,
                    raw_text=raw_matched,
                    normalized_value=normalized_code,
                    span=(start_char, end_char),
                    line_number=line_num,
                    context_snippet=snippet,
                    section=section,
                    extra={
                        "doc_number": doc_number,
                        "doc_suffix": doc_suffix,
                    },
                )
            )

        return results
