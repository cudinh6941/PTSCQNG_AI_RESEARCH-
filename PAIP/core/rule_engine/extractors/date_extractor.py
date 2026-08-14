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

    # Pattern 1: (Thứ ..., ) ngày DD tháng MM năm YYYY
    _FULL_TEXT_DATE = re.compile(
        r"(?:(Thứ\s+(?:Hai|Ba|Tư|Năm|Sáu|Bảy|7|6|5|4|3|2)|Chủ\s*nhật|CN)[,\s]*)?(?:ngày|Ngày)\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})",
        re.IGNORECASE | re.UNICODE,
    )

    # Pattern 2: (Thứ ..., ) DD/MM/YYYY
    _SLASH_DATE = re.compile(
        r"(?:(Thứ\s+(?:Hai|Ba|Tư|Năm|Sáu|Bảy|7|6|5|4|3|2)|Chủ\s*nhật|CN)[,\s]*)?\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b",
        re.IGNORECASE | re.UNICODE,
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

        def add_date(raw_str: str, d: int, m: int, y: int, span: tuple[int, int], dow_text: str | None = None):
            if span in found_spans:
                return
            
            is_valid_date = True
            dt_val = None
            try:
                dt_val = datetime.date(y, m, d)
            except ValueError:
                is_valid_date = False

            found_spans.add(span)
            start_char, end_char = span

            # Xác định ngữ cảnh & vai trò qua tiền tố ngữ cảnh (prefix_ctx)
            prefix_ctx = text[max(0, start_char - 80):start_char].lower()
            
            # Cắt bớt phần trước dấu chấm hoặc xuống dòng gần nhất để tránh lấy nhầm ngữ cảnh câu trước
            last_dot = max(prefix_ctx.rfind("."), prefix_ctx.rfind("\n"))
            if last_dot != -1:
                prefix_ctx = prefix_ctx[last_dot + 1:]

            role = "general"
            section = "body"

            check_str = (prefix_ctx + raw_str).lower()

            if any(kw in check_str for kw in ("hạn nộp", "hạn chót", "thời hạn nộp", "trước ngày", "chậm nhất ngày", "chậm nhất")):
                role = "deadline"
            elif any(kw in check_str for kw in ("hiệu lực từ", "bắt đầu từ", "kể từ ngày")):
                role = "effective_start"
            elif any(kw in check_str for kw in ("đến ngày", "đến hết ngày", "kết thúc ngày", "nghiệm thu ngày", "thanh lý ngày")):
                role = "completion_date"
            elif any(kw in check_str for kw in ("quảng ngãi, ngày", "hà nội, ngày", "tp.hcm, ngày", "tp hcm, ngày", "ngày ban hành", "ngày ký", "ngày lập", "lập ngày")) or start_char < min(150, total_len * 0.20):
                role = "issued_date"
                section = "header"

            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.DATE,
                    raw_text=raw_str,
                    normalized_value=dt_val.isoformat() if dt_val else None,
                    span=span,
                    context_snippet=snippet,
                    section=section,
                    extra={
                        "date_obj": dt_val,
                        "day": d,
                        "month": m,
                        "year": y,
                        "role": role,
                        "is_valid_date": is_valid_date,
                        "day_of_week_text": dow_text,
                    },
                )
            )

        # 1. Quét text date (ngày ... tháng ... năm ...)
        for match in self._FULL_TEXT_DATE.finditer(text):
            dow = match.group(1)
            d = int(match.group(2))
            m = int(match.group(3))
            y = int(match.group(4))
            add_date(match.group(0), d, m, y, match.span(), dow)

        # 2. Quét slash date (DD/MM/YYYY)
        for match in self._SLASH_DATE.finditer(text):
            dow = match.group(1)
            d = int(match.group(2))
            m = int(match.group(3))
            y = int(match.group(4))
            add_date(match.group(0), d, m, y, match.span(), dow)

        # Sắp xếp theo vị trí xuất hiện
        results.sort(key=lambda x: x.span[0])
        return results
