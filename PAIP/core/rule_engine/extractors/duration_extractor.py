"""
Duration Extractor — Bóc tách khoảng thời gian (ngày, tháng, năm).
"""

from __future__ import annotations

import datetime
import re
from typing import Any

from .base_extractor import BaseEntityExtractor, EntityType, ExtractedEntity


class DurationExtractor(BaseEntityExtractor):
    """Bóc tách các khoảng thời gian (VD: 3 ngày, 6 tháng, 1 năm)."""

    # Pattern: số (chữ số hoặc chữ viết) + khoảng trắng + (ngày|tháng|năm)
    # Loại trừ các trường hợp nằm trong chuỗi ngày tháng (VD: "ngày 31 tháng", "tháng 2 năm")
    _DURATION_PATTERN = re.compile(
        r"(?<!ngày\s)(?<!tháng\s)(?<!năm\s)\b(\d{1,3})\s+(ngày|tháng|năm)\b",
        re.IGNORECASE | re.UNICODE,
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.DURATION

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text:
            return []

        results: list[ExtractedEntity] = []
        total_len = len(text)

        for match in self._DURATION_PATTERN.finditer(text):
            val_str = match.group(1)
            unit_str = match.group(2).lower()
            
            try:
                val = int(val_str)
            except ValueError:
                continue

            delta: datetime.timedelta | None = None
            if unit_str == "ngày":
                delta = datetime.timedelta(days=val)
            elif unit_str == "tháng":
                # Xấp xỉ 30 ngày / tháng
                delta = datetime.timedelta(days=val * 30)
            elif unit_str == "năm":
                # Xấp xỉ 365 ngày / năm
                delta = datetime.timedelta(days=val * 365)
                
            if delta is None:
                continue

            span = match.span()
            start_char, end_char = span
            
            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.DURATION,
                    raw_text=match.group(0),
                    normalized_value=val,
                    span=span,
                    context_snippet=snippet,
                    extra={
                        "value": val,
                        "unit": unit_str,
                        "delta": delta,
                    },
                )
            )

        return results
