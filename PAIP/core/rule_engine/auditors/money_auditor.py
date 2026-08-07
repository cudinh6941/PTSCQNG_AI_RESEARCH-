"""
CA-002: Money Number vs Words Consistency Auditor.

Kiểm tra sự sai lệch giá trị giữa số tiền ghi bằng số và số tiền ghi bằng chữ.
"""

from __future__ import annotations

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix, ExtractedEntity
from .base_auditor import AuditConflict, BaseAuditor


class MoneyAuditor(BaseAuditor):
    """
    Quy tắc CA-002: Đối soát số tiền bằng số và số tiền bằng chữ.

    Ví dụ:
    - Bằng số: 150.000.000 VNĐ
    - Bằng chữ: Một trăm năm mươi hai triệu đồng (Lệch 2.000.000 VNĐ)
    """

    @property
    def rule_id(self) -> str:
        return "CA-002"

    @property
    def rule_name(self) -> str:
        return "Money Number vs Words"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        monies = matrix.monies
        if not monies:
            return []

        numeric_monies = [m for m in monies if m.extra.get("form") == "numeric"]
        words_monies = [m for m in monies if m.extra.get("form") == "words"]

        if not numeric_monies or not words_monies:
            return []

        conflicts: list[AuditConflict] = []
        matched_words: set[int] = set()

        for num_ent in numeric_monies:
            num_val = float(num_ent.normalized_value or 0)
            if num_val <= 0:
                continue

            # Tìm thực thể bằng chữ gần nhất (trong phạm vi 250 ký tự phía sau hoặc phía trước)
            num_start, num_end = num_ent.span
            closest_word: ExtractedEntity | None = None
            min_dist = float("inf")

            for i, w_ent in enumerate(words_monies):
                if i in matched_words:
                    continue
                w_start, w_end = w_ent.span
                dist = abs(w_start - num_end)
                if dist < 250 and dist < min_dist:
                    min_dist = dist
                    closest_word = w_ent

            if closest_word is not None:
                w_val = float(closest_word.normalized_value or 0)
                if w_val > 0 and num_val != w_val:
                    diff = abs(num_val - w_val)
                    conflicts.append(
                        AuditConflict(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            severity=RuleSeverity.ERROR,
                            description=(
                                f"Lệch số tiền bằng số và bằng chữ: Số ghi '{num_ent.raw_text}' "
                                f"nhưng Chữ ghi '{closest_word.raw_text}' (Chênh lệch: {diff:,.0f} VNĐ)"
                            ),
                            original_text=closest_word.raw_text,
                            suggested_fix=f"[Kiểm tra lại] Giá trị số: {num_val:,.0f} VNĐ vs Giá trị chữ: {w_val:,.0f} VNĐ",
                            explanation=(
                                f"Phát hiện mâu thuẫn tài chính nghiêm trọng giữa phần ghi bằng số ({num_val:,.0f} VNĐ) "
                                f"và phần diễn giải bằng chữ ({w_val:,.0f} VNĐ), chênh lệch {diff:,.0f} VNĐ. "
                                f"Trong văn bản pháp lý & hợp đồng, điều này có thể dẫn đến vô hiệu điều khoản thanh toán hoặc tranh chấp tài chính."
                            ),
                            side_a={
                                "label": "Bằng số",
                                "value": f"{num_val:,.0f} VNĐ",
                                "raw_text": num_ent.raw_text,
                            },
                            side_b={
                                "label": "Bằng chữ",
                                "value": f"{w_val:,.0f} VNĐ",
                                "raw_text": closest_word.raw_text,
                            },
                            span=closest_word.span,
                            extra={
                                "numeric_amount": num_val,
                                "words_amount": w_val,
                                "difference": diff,
                            },
                        )
                    )

        return conflicts
