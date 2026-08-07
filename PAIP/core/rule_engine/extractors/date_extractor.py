"""
Date Extractor — Bóc tách ngày tháng năm & gán nhãn ngữ cảnh thời gian.
"""

from __future__ import annotations

import datetime
import re
from typing import Any

from .base_extractor import BaseEntityExtractor, EntityType, ExtractedEntity


class DateExtractor(BaseEntityExtractor):
    """Bóc tách các mốc ngày tháng năm và phân loại vai trò (Ngày ban hành, Hạn nộp, v.v.)."""

    # Pattern 1: ngày DD tháng MM năm YYYY (hoặc DD/MM/YYYY)
    _FULL_TEXT_DATE = re.compile(
        r"(?:ngày|Ngày)\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})",
        re.IGNORECASE | re.UNICODE,
    )

    # Pattern 2: DD/MM/YYYY hoặc DD-MM-YYYY hoặc DD.MM.YYYY
    _SLASH_DATE = re.compile(
        r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b",
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.DATE

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text:
            return []

        results: list[ExtractedEntity] = []
        total_len = len(text)
        found_spans: set[tuple[int, int]] = set()

        def add_date(raw_str: str, d: int, m: int, y: int, span: tuple[int, int]):
            if span in found_spans:
                return
            try:
                dt_val = datetime.date(y, m, d)
            except ValueError:
                # Ngày không hợp lệ (ví dụ: ngày 31 tháng 2)
                return

            found_spans.add(span)
            start_char, end_char = span

            # Xác định ngữ cảnh & vai trò qua tiền tố ngữ cảnh (prefix_ctx)
            prefix_ctx = text[max(0, start_char - 80):start_char].lower()

            role = "general"
            section = "body"

            if any(kw in prefix_ctx for kw in ("hạn nộp", "hạn chót", "thời hạn nộp", "trước ngày", "chậm nhất ngày", "chậm nhất")):
                role = "deadline"
            elif any(kw in prefix_ctx for kw in ("hiệu lực từ", "bắt đầu từ", "kể từ ngày")):
                role = "effective_start"
            elif any(kw in prefix_ctx for kw in ("đến ngày", "đến hết ngày", "kết thúc ngày", "nghiệm thu ngày", "thanh lý ngày")):
                role = "completion_date"
            elif any(kw in prefix_ctx for kw in ("quảng ngãi, ngày", "hà nội, ngày", "ngày ban hành", "ngày ký", "ngày lập")) or start_char < min(150, total_len * 0.20):
                role = "issued_date"
                section = "header"

            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.DATE,
                    raw_text=raw_str,
                    normalized_value=dt_val.isoformat(),
                    span=span,
                    context_snippet=snippet,
                    section=section,
                    extra={
                        "date_obj": dt_val,
                        "day": d,
                        "month": m,
                        "year": y,
                        "role": role,
                    },
                )
            )

        # 1. Quét text date (ngày ... tháng ... năm ...)
        for match in self._FULL_TEXT_DATE.finditer(text):
            d = int(match.group(1))
            m = int(match.group(2))
            y = int(match.group(3))
            add_date(match.group(0), d, m, y, match.span())

        # 2. Quét slash date (DD/MM/YYYY)
        for match in self._SLASH_DATE.finditer(text):
            d = int(match.group(1))
            m = int(match.group(2))
            y = int(match.group(3))
            add_date(match.group(0), d, m, y, match.span())

        # Sắp xếp theo vị trí xuất hiện
        results.sort(key=lambda x: x.span[0])
        return results
