"""
Clause Reference Extractor — Bóc tách tham chiếu Điều/Khoản & danh mục Điều thực tế.
"""

from __future__ import annotations

import re
from typing import Any

from .base_extractor import BaseEntityExtractor, EntityType, ExtractedEntity


class ClauseRefExtractor(BaseEntityExtractor):
    """
    Bóc tách các tham chiếu điều khoản trong văn bản và danh sách các Điều thực tế.

    Hỗ trợ phát hiện lỗi tham chiếu 'Điều ma' (Ghost Clause Reference) cho CA-007.
    """

    # Pattern nhận diện đề mục Điều thực tế: "Điều 1.", "Điều 2:", "ĐIỀU 10 -"
    _CLAUSE_HEADING_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:Điều|ĐIỀU)\s+(\d{1,3})[\.\:\-\s]",
        re.UNICODE,
    )

    # Pattern bóc tách tham chiếu: "Điều 15", "Khoản 2 Điều 10", "Điểm a Khoản 1 Điều 5"
    _CLAUSE_REF_PATTERN = re.compile(
        r"(?:(?:Điểm\s+[a-zđ]\s+)?(?:Khoản\s+\d+\s+)?(?:Mục\s+\d+(?:\.\d+)?\s+)?)?"
        r"(?:Điều|điều)\s+(\d{1,3})",
        re.UNICODE,
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.CLAUSE_REF

    def extract_actual_clauses(self, text: str) -> list[int]:
        """Trích xuất danh sách số thứ tự các Điều thực tế được định nghĩa trong văn bản."""
        if not text:
            return []
        clauses = set()
        for match in self._CLAUSE_HEADING_PATTERN.finditer(text):
            try:
                c_num = int(match.group(1))
                clauses.add(c_num)
            except ValueError:
                continue
        return sorted(list(clauses))

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text:
            return []

        results: list[ExtractedEntity] = []
        total_len = len(text)

        # Lấy danh sách các heading để loại trừ không nhầm heading là reference
        heading_spans: set[tuple[int, int]] = set()
        for h_match in self._CLAUSE_HEADING_PATTERN.finditer(text):
            heading_spans.add(h_match.span())

        for match in self._CLAUSE_REF_PATTERN.finditer(text):
            span = match.span()
            # Bỏ qua nếu đây chính là dòng tiêu đề Điều
            if any(h_start <= span[0] and span[1] <= h_end for h_start, h_end in heading_spans):
                continue

            raw_ref = match.group(0).strip()
            clause_num = int(match.group(1))
            start_char, end_char = span

            # Kiểm tra xem có phải trích dẫn Luật / Nghị định bên ngoài hay không
            suffix_ctx = text[end_char:min(total_len, end_char + 100)].lower()
            is_external_law = any(
                kw in suffix_ctx
                for kw in (
                    "luật",
                    "nghị định",
                    "thông tư",
                    "quyết định số",
                    "bộ luật",
                    "quy định pháp luật",
                )
            )

            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.CLAUSE_REF,
                    raw_text=raw_ref,
                    normalized_value=clause_num,
                    span=span,
                    context_snippet=snippet,
                    section="body",
                    extra={
                        "clause_number": clause_num,
                        "is_external_law": is_external_law,
                    },
                )
            )

        return results
