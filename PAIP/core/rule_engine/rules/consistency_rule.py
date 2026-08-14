"""
Level 2 Rule: Consistency & Cross-Audit Rule.

Điều phối quá trình bóc tách Ma trận Thực thể (Entity Matrix),
chạy các bộ đối soát chéo (Auditors) và sinh các vi phạm CONSISTENCY.
"""

from __future__ import annotations

import time

from ..auditors import AuditConflict, run_cross_audit
from ..base import BaseRule, RuleResult, RuleSeverity, RuleType, RuleViolation
from ..context import RuleContext
from ..extractors import extract_entity_matrix


class ConsistencyRule(BaseRule):
    """
    Rule Level 2: Kiểm tra tính nhất quán thông tin nội tại văn bản.

    - Bóc tách Ma trận Thực thể (Số hiệu, Tiền tệ, Ngày tháng, Tỷ lệ %, Điều khoản).
    - Đối soát chéo qua các Audit Rules (CA-001 -> CA-007).
    - Tạo các RuleViolation dạng CONSISTENCY và cảnh báo tiêm vào LLM Prompt.
    """

    def __init__(self, *, enabled: bool = True, severity: RuleSeverity = RuleSeverity.ERROR):
        super().__init__(enabled=enabled, severity=severity)

    @property
    def rule_type(self) -> RuleType:
        return RuleType.CONSISTENCY

    @property
    def name(self) -> str:
        return "Consistency & Cross-Audit Rule"

    def evaluate(self, context: RuleContext) -> RuleResult:
        if not self.enabled or not context.text or not context.text.strip():
            return RuleResult()

        start_time = time.perf_counter()

        # 1. Bóc tách Ma trận Thực thể
        matrix = extract_entity_matrix(context.text)

        # 2. Chạy đối soát chéo
        conflicts = run_cross_audit(matrix, context.text)

        # 3. Chuyển đổi thành RuleViolation
        violations: list[RuleViolation] = []
        prompt_lines: list[str] = []

        for c in conflicts:
            if c.rule_id == "CALCULATOR_SIDECAR":
                # Đây không phải lỗi, đây là dữ liệu cung cấp cho LLM (Calculator Sidecar)
                prompt_lines.append(c.description)
                continue

            pos = None
            if c.span and c.span != (0, 0):
                pos = {"start_char": c.span[0], "end_char": c.span[1]}

            violations.append(
                RuleViolation(
                    rule_id=c.rule_id,
                    rule_type=RuleType.CONSISTENCY,
                    severity=c.severity,
                    original_text=c.original_text,
                    suggested_fix=c.suggested_fix,
                    explanation=c.explanation or c.description,
                    position=pos,
                    side_a=c.side_a,
                    side_b=c.side_b,
                )
            )

            # Cảnh báo các rule còn lại (như CA-001, CA-002, ...)
            prompt_lines.append(f"- [{c.rule_id}] {c.description}")

        # 4. Tạo prompt injection nếu có xung đột cần lưu ý
        prompt_injection = ""
        if prompt_lines:
            prompt_injection = (
                "\n[CONTEXT BỔ SUNG TỪ HỆ THỐNG RULE ENGINE — HÃY SỬ DỤNG THÔNG TIN NÀY]:\n"
                + "\n".join(prompt_lines)
                + "\n\n"
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return RuleResult(
            violations=violations,
            detected_terms=[],
            whitelist_terms=[],
            prompt_injection=prompt_injection,
            processing_time_ms=elapsed_ms,
        )
