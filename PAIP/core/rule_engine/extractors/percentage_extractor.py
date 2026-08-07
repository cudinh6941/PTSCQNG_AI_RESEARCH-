"""
Percentage Extractor — Bóc tách tỷ lệ % thanh toán, tạm ứng, bảo hành.
"""

from __future__ import annotations

import re
from typing import Any

from .base_extractor import BaseEntityExtractor, EntityType, ExtractedEntity


class PercentageExtractor(BaseEntityExtractor):
    """Bóc tách các tỷ lệ % (đặc biệt trong các điều khoản thanh toán & tiến độ)."""

    _PERCENT_PATTERN = re.compile(
        r"(\b\d{1,3}(?:[.,]\d+)?)\s*%",
        re.UNICODE,
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.PERCENTAGE

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text:
            return []

        results: list[ExtractedEntity] = []
        total_len = len(text)

        for match in self._PERCENT_PATTERN.finditer(text):
            raw_str = match.group(0).strip()
            num_str = match.group(1).replace(",", ".")
            try:
                pct_val = float(num_str)
            except ValueError:
                continue

            start_char, end_char = match.span()

            # Lấy ngữ cảnh xung quanh để gán nhãn
            prefix_ctx = text[max(0, start_char - 80):start_char].lower()
            suffix_ctx = text[end_char:min(total_len, end_char + 80)].lower()
            combined = prefix_ctx + " " + suffix_ctx

            group = "general"
            label = "Tỷ lệ %"

            if any(kw in prefix_ctx for kw in ("tạm ứng", "ứng trước")):
                group = "payment_schedule"
                label = "Tạm ứng"
            elif any(kw in prefix_ctx for kw in ("đợt 1", "lần 1", "giai đoạn 1")):
                group = "payment_schedule"
                label = "Đợt 1"
            elif any(kw in prefix_ctx for kw in ("đợt 2", "lần 2", "giai đoạn 2")):
                group = "payment_schedule"
                label = "Đợt 2"
            elif any(kw in prefix_ctx for kw in ("đợt 3", "lần 3", "giai đoạn 3")):
                group = "payment_schedule"
                label = "Đợt 3"
            elif any(kw in prefix_ctx for kw in ("đợt 4", "lần 4", "giai đoạn 4")):
                group = "payment_schedule"
                label = "Đợt 4"
            elif any(kw in prefix_ctx for kw in ("quyết toán", "thanh lý", "nghiệm thu cuối")):
                group = "payment_schedule"
                label = "Đợt cuối / Quyết toán"
            elif any(kw in combined for kw in ("bảo hành", "giữ lại bảo hành")):
                group = "retention"
                label = "Bảo hành"
            elif any(kw in combined for kw in ("thuế gtgt", "thuế vat", "vat")):
                group = "tax"
                label = "Thuế VAT"

            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.PERCENTAGE,
                    raw_text=raw_str,
                    normalized_value=pct_val,
                    span=(start_char, end_char),
                    context_snippet=snippet,
                    section="body",
                    extra={
                        "percentage": pct_val,
                        "group": group,
                        "label": label,
                    },
                )
            )

        return results
