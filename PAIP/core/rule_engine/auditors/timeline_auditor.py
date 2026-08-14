"""
CA-003: Timeline Logic Auditor (Calculator Sidecar).

Thay vì tự động sinh lỗi, Auditor này tính toán sẵn mọi tổ hợp 
Ngày + Thời gian (Date Math) và tạo ra Bảng Tra Cứu (Lookup Table) 
cho LLM. LLM sẽ dùng bảng này để đối chiếu ngữ cảnh hợp đồng 
mà không cần tự làm toán.
"""

from __future__ import annotations

import datetime

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix
from .base_auditor import AuditConflict, BaseAuditor


class TimelineAuditor(BaseAuditor):
    """
    Quy tắc CA-003: Tính toán dòng thời gian (Date Math Lookup Table).
    """

    @property
    def rule_id(self) -> str:
        return "CA-003"

    @property
    def rule_name(self) -> str:
        return "Timeline Logic (Calculator Sidecar)"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        conflicts: list[AuditConflict] = []

        # Chỉ lấy các ngày hợp lệ và có ngày tháng cụ thể
        valid_dates = [
            d for d in matrix.dates 
            if d.extra.get("is_valid_date", True) and d.extra.get("date_obj")
        ]
        
        # Chỉ lấy các khoảng thời gian hợp lệ (lọc trùng lặp text nếu cần)
        durations = matrix.durations

        if valid_dates and durations:
            math_lines = [
                "[BẢNG TRA CỨU NGÀY THÁNG - HÃY SỬ DỤNG BẢNG NÀY ĐỂ KIỂM TRA TÍNH NHẤT QUÁN CỦA CÁC ĐIỀU KHOẢN THỜI HẠN. KHÔNG TỰ TÍNH TOÁN:]"
            ]
            
            # Để tránh bảng quá dài nếu có quá nhiều ngày/thời hạn, ta có thể dùng set() để loại bỏ trùng lặp
            unique_combinations = set()

            for d in valid_dates:
                dt_obj: datetime.date = d.extra.get("date_obj")
                date_str = dt_obj.strftime("%d/%m/%Y")
                
                for dur in durations:
                    delta: datetime.timedelta = dur.extra.get("delta")
                    if delta:
                        dur_str = dur.raw_text.lower().strip()
                        combo_key = (date_str, dur_str)
                        
                        if combo_key not in unique_combinations:
                            unique_combinations.add(combo_key)
                            res_dt = dt_obj + delta
                            math_lines.append(
                                f"- Ngày {date_str} + {dur_str} = Ngày {res_dt.strftime('%d/%m/%Y')}"
                            )
            
            if unique_combinations:
                conflicts.append(
                    AuditConflict(
                        rule_id="CALCULATOR_SIDECAR",
                        rule_name="Calculator Sidecar",
                        severity=RuleSeverity.INFO,
                        description="\n".join(math_lines),
                        original_text="",
                        suggested_fix="",
                    )
                )

        # 2. Bắt lỗi nghịch lý thời gian cơ bản (Ngày ban hành > Hạn chót)
        issued_dates = [d for d in valid_dates if d.extra.get("role") == "issued_date"]
        deadlines = [d for d in valid_dates if d.extra.get("role") in ("deadline", "completion_date")]

        if issued_dates and deadlines:
            primary_issued = issued_dates[0]
            issued_dt = primary_issued.extra.get("date_obj")

            for dl in deadlines:
                dl_dt = dl.extra.get("date_obj")
                if issued_dt and dl_dt and issued_dt > dl_dt:
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

        # Trả về các mâu thuẫn (cả Bảng tra cứu LLM và Lỗi nghịch lý nếu có)
        return conflicts
