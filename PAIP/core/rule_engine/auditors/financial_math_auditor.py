"""
Financial Math Auditor (Calculator Sidecar).

Tính toán sẵn các tổ hợp phép nhân giữa Số Tiền (Money) và Tỷ lệ % (Percentage) 
để tạo Bảng tra cứu tài chính cho LLM, giúp LLM đối soát các điều khoản thanh toán
mà không cần tự làm toán.
"""

from __future__ import annotations

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix
from .base_auditor import AuditConflict, BaseAuditor


class FinancialMathAuditor(BaseAuditor):
    """
    Tạo bảng tính toán sẵn: Số Tiền * Tỷ lệ % = Kết quả.
    """

    @property
    def rule_id(self) -> str:
        return "CALCULATOR_SIDECAR"

    @property
    def rule_name(self) -> str:
        return "Financial Math Sidecar"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        monies = matrix.monies
        percentages = matrix.percentages

        if not monies or not percentages:
            return []

        # Lọc các số tiền hợp lệ (> 0)
        valid_monies = []
        seen_money_vals = set()
        for m in monies:
            val = float(m.normalized_value or 0)
            if val > 0 and val not in seen_money_vals:
                seen_money_vals.add(val)
                valid_monies.append(m)

        # Lọc các % hợp lệ (> 0 và < 100)
        valid_pcts = []
        seen_pct_vals = set()
        for p in percentages:
            val = float(p.normalized_value or 0)
            if 0 < val <= 100 and val not in seen_pct_vals:
                seen_pct_vals.add(val)
                valid_pcts.append(p)

        if not valid_monies or not valid_pcts:
            return []

        math_lines = [
            "[BẢNG TRA CỨU TÀI CHÍNH - HÃY SỬ DỤNG BẢNG NÀY ĐỂ ĐỐI SOÁT CÁC ĐIỀU KHOẢN THANH TOÁN / BẢO HÀNH. KHÔNG TỰ TÍNH TOÁN:]"
        ]

        for m in valid_monies:
            m_val = float(m.normalized_value or 0)
            m_str = f"{m_val:,.0f} {m.extra.get('currency', 'VNĐ')}"
            
            for p in valid_pcts:
                p_val = float(p.normalized_value or 0)
                p_str = f"{p_val:g}%"
                
                result = m_val * (p_val / 100.0)
                res_str = f"{result:,.0f} {m.extra.get('currency', 'VNĐ')}"
                
                math_lines.append(f"- {m_str} * {p_str} = {res_str}")

        return [
            AuditConflict(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=RuleSeverity.INFO,
                description="\n".join(math_lines),
                original_text="",
                suggested_fix="",
            )
        ]
