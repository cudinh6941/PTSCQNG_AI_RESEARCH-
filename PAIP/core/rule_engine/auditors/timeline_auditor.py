"""
CA-003: Timeline Logic Auditor.

Kiểm tra nghịch lý logic dòng thời gian trong văn bản hành chính & thương mại.
"""

from __future__ import annotations

import datetime

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix, ExtractedEntity
from .base_auditor import AuditConflict, BaseAuditor


class TimelineAuditor(BaseAuditor):
    """
    Quy tắc CA-003: Kiểm tra nghịch lý dòng thời gian.

    Ví dụ:
    - Ngày ban hành / ký công văn: 10/08/2026
    - Hạn nộp hồ sơ thầu: 08/08/2026 (Nghịch lý: Hạn chót trước ngày ban hành)
    """

    @property
    def rule_id(self) -> str:
        return "CA-003"

    @property
    def rule_name(self) -> str:
        return "Timeline Logic"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        dates = matrix.dates
        if len(dates) < 2:
            return []

        conflicts: list[AuditConflict] = []

        issued_dates = [d for d in dates if d.extra.get("role") == "issued_date"]
        deadlines = [d for d in dates if d.extra.get("role") in ("deadline", "completion_date")]

        if not issued_dates or not deadlines:
            return []

        primary_issued = issued_dates[0]
        issued_dt: datetime.date = primary_issued.extra.get("date_obj")

        for dl in deadlines:
            dl_dt: datetime.date = dl.extra.get("date_obj")
            if not issued_dt or not dl_dt:
                continue

            # Nếu ngày ban hành sau hạn nộp hồ sơ
            if issued_dt > dl_dt:
                role_label = "Hạn nộp hồ sơ / Hạn chót" if dl.extra.get("role") == "deadline" else "Ngày hoàn thành"
                conflicts.append(
                    AuditConflict(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=RuleSeverity.ERROR,
                        description=(
                            f"Nghịch lý thời gian: Ngày ban hành ({primary_issued.raw_text}) "
                            f"muộn hơn {role_label} ({dl.raw_text})"
                        ),
                        original_text=dl.raw_text,
                        suggested_fix=f"[Kiểm tra lại hạn nộp] Phải sau ngày ban hành ({primary_issued.raw_text})",
                        explanation=(
                            f"Văn bản được lập/ban hành vào ngày {primary_issued.raw_text} ({issued_dt.isoformat()}), "
                            f"nhưng {role_label} lại đặt vào ngày {dl.raw_text} ({dl_dt.isoformat()}). "
                            f"Điều này tạo ra mâu thuẫn thời gian nghiêm trọng (hạn nộp trước khi văn bản có hiệu lực)."
                        ),
                        side_a={
                            "label": "Ngày ban hành / Ký duyệt",
                            "value": primary_issued.raw_text,
                            "date_iso": issued_dt.isoformat(),
                        },
                        side_b={
                            "label": role_label,
                            "value": dl.raw_text,
                            "date_iso": dl_dt.isoformat(),
                        },
                        span=dl.span,
                        extra={
                            "issued_date": issued_dt.isoformat(),
                            "deadline_date": dl_dt.isoformat(),
                        },
                    )
                )

        return conflicts
