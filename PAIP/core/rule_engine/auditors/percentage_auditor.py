"""
CA-005: Payment Percentage Total Consistency Auditor.

Kiểm tra tổng tỷ lệ % của các đợt thanh toán, tạm ứng, quyết toán trong hợp đồng.
"""

from __future__ import annotations

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix, ExtractedEntity
from .base_auditor import AuditConflict, BaseAuditor


class PercentageAuditor(BaseAuditor):
    """
    Quy tắc CA-005: Kiểm tra tổng tỷ lệ % các đợt thanh toán phải bằng 100%.

    Ví dụ:
    - Đợt 1 (Tạm ứng): 30%
    - Đợt 2 (Giao hàng): 50%
    - Đợt 3 (Nghiệm thu): 30%
    -> Tổng = 110% (Vượt mức 100% -> Lỗi tài chính nghiêm trọng)
    """

    @property
    def rule_id(self) -> str:
        return "CA-005"

    @property
    def rule_name(self) -> str:
        return "Payment Percentage Total"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        percentages = matrix.percentages
        if len(percentages) < 2:
            return []

        payment_items = [p for p in percentages if p.extra.get("group") == "payment_schedule"]
        if len(payment_items) < 2:
            return []

        total_pct = sum(float(p.normalized_value or 0) for p in payment_items)

        # Cho phép sai số rất nhỏ do float rounding (0.01)
        if abs(total_pct - 100.0) > 0.01:
            diff = total_pct - 100.0
            last_item = payment_items[-1]

            breakdown_str = " + ".join([f"{p.extra.get('label', 'Đợt')}: {p.normalized_value}%" for p in payment_items])

            return [
                AuditConflict(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=RuleSeverity.ERROR,
                    description=(
                        f"Tổng tỷ lệ thanh toán không đạt 100%: Tổng = {total_pct:.1f}% "
                        f"({breakdown_str} = {total_pct:.1f}%)"
                    ),
                    original_text=last_item.raw_text,
                    suggested_fix=f"[Cân đối lại tỷ lệ %] Tổng các đợt hiện tại là {total_pct:.1f}%, cần điều chỉnh về đúng 100%",
                    explanation=(
                        f"Phát hiện tổng các đợt thanh toán/tạm ứng không bằng 100% ({breakdown_str} = {total_pct:.1f}%, lệch {diff:+.1f}%). "
                        f"Điều này gây rủi ro thất thoát hoặc vướng mắc thủ tục giải ngân tài chính."
                    ),
                    side_a={
                        "label": "Tổng tính toán thực tế",
                        "value": f"{total_pct:.1f}%",
                        "breakdown": breakdown_str,
                    },
                    side_b={
                        "label": "Quy chuẩn bắt buộc",
                        "value": "100.0%",
                    },
                    span=last_item.span,
                    extra={
                        "total_percentage": total_pct,
                        "difference": diff,
                        "milestones": [
                            {"label": p.extra.get("label"), "value": p.normalized_value}
                            for p in payment_items
                        ],
                    },
                )
            ]

        return []
