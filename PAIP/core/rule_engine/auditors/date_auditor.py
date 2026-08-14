"""
CA-006: Date Correctness Auditor.

Kiểm tra tính hợp lệ của ngày tháng (VD: 31/02) và sự khớp nhau giữa Thứ và Ngày.
"""

from __future__ import annotations

import datetime
import unicodedata

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix, ExtractedEntity
from .base_auditor import AuditConflict, BaseAuditor


class DateAuditor(BaseAuditor):
    """
    Quy tắc CA-006: Kiểm tra tính đúng đắn của Ngày.

    - Ngày không tồn tại (vd 31/02/2026).
    - Thứ và Ngày không khớp (vd: Thứ Hai, 10/08/2026, nhưng thực tế là Thứ Ba).
    """

    @property
    def rule_id(self) -> str:
        return "CA-006"

    @property
    def rule_name(self) -> str:
        return "Date Correctness"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        conflicts: list[AuditConflict] = []
        
        # Ánh xạ từ string sang số nguyên của `weekday()` (0 = Thứ 2, 6 = Chủ nhật)
        dow_map = {
            "thứ hai": 0, "thứ 2": 0,
            "thứ ba": 1, "thứ 3": 1,
            "thứ tư": 2, "thứ 4": 2,
            "thứ năm": 3, "thứ 5": 3,
            "thứ sáu": 4, "thứ 6": 4,
            "thứ bảy": 5, "thứ 7": 5,
            "chủ nhật": 6, "cn": 6
        }
        
        # Tên chuẩn để báo lỗi
        dow_names = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

        for d in matrix.dates:
            is_valid = d.extra.get("is_valid_date", True)
            raw_val = d.raw_text
            
            if not is_valid:
                conflicts.append(
                    AuditConflict(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=RuleSeverity.ERROR,
                        description=f"Ngày không tồn tại trên thực tế: {raw_val}",
                        original_text=raw_val,
                        suggested_fix="[Kiểm tra lại lịch] Ngày này không hợp lệ",
                        explanation=f"Ngày {d.extra.get('day')}/{d.extra.get('month')}/{d.extra.get('year')} không tồn tại trên lịch.",
                        span=d.span,
                    )
                )
                continue
            
            # Kiểm tra Thứ nếu có
            dow_text = d.extra.get("day_of_week_text")
            dt_obj: datetime.date | None = d.extra.get("date_obj")
            
            if dow_text and dt_obj:
                clean_dow = unicodedata.normalize("NFC", dow_text.lower().strip())
                expected_dow_idx = dow_map.get(clean_dow)
                
                if expected_dow_idx is not None:
                    actual_dow_idx = dt_obj.weekday()
                    
                    if expected_dow_idx != actual_dow_idx:
                        actual_dow_name = dow_names[actual_dow_idx]
                        conflicts.append(
                            AuditConflict(
                                rule_id=self.rule_id,
                                rule_name=self.rule_name,
                                severity=RuleSeverity.WARNING,
                                description=f"Thứ và Ngày không khớp: {raw_val}",
                                original_text=raw_val,
                                suggested_fix=f"{actual_dow_name}, ngày {dt_obj.strftime('%d/%m/%Y')}",
                                explanation=f"Văn bản ghi là '{dow_text}', nhưng theo lịch thì ngày {dt_obj.strftime('%d/%m/%Y')} là {actual_dow_name}.",
                                span=d.span,
                            )
                        )
                        
        return conflicts
