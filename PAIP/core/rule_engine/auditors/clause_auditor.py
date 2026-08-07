"""
CA-007: Ghost Clause Reference Auditor.

Kiểm tra và phát hiện các tham chiếu điều khoản không tồn tại trong cấu trúc văn bản.
"""

from __future__ import annotations

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix, ExtractedEntity
from .base_auditor import AuditConflict, BaseAuditor


class ClauseAuditor(BaseAuditor):
    """
    Quy tắc CA-007: Phát hiện tham chiếu 'Điều ma' (Ghost Clause Reference).

    Ví dụ:
    - Văn bản chỉ có 10 Điều (Điều 1 đến Điều 10).
    - Nhưng tại trang 3 ghi: 'Căn cứ quy định tại Điều 15 Hợp đồng này...'
    -> Điều 15 không tồn tại -> Lỗi logic tham chiếu văn bản.
    """

    @property
    def rule_id(self) -> str:
        return "CA-007"

    @property
    def rule_name(self) -> str:
        return "Ghost Clause Reference"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        actual_clauses = matrix.actual_clauses
        if not actual_clauses:
            # Không phát hiện cấu trúc đề mục Điều trong văn bản (ví dụ công văn ngắn không chia Điều)
            return []

        max_clause = max(actual_clauses)
        conflicts: list[AuditConflict] = []

        for ref in matrix.clause_refs:
            # Bỏ qua nếu là trích dẫn luật/nghị định bên ngoài
            if ref.extra.get("is_external_law"):
                continue

            clause_num = ref.extra.get("clause_number", 0)
            if clause_num > max_clause:
                conflicts.append(
                    AuditConflict(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=RuleSeverity.ERROR,
                        description=(
                            f"Tham chiếu điều khoản không tồn tại: Trích dẫn '{ref.raw_text}' "
                            f"nhưng văn bản chỉ có đến Điều {max_clause}"
                        ),
                        original_text=ref.raw_text,
                        suggested_fix=f"[Kiểm tra lại số Điều] Văn bản hiện chỉ có từ Điều 1 đến Điều {max_clause}",
                        explanation=(
                            f"Đoạn văn trích dẫn '{ref.raw_text}', tuy nhiên trong toàn bộ văn bản "
                            f"chỉ có tổng cộng {len(actual_clauses)} Điều (Điều {min(actual_clauses)} đến Điều {max_clause}). "
                            f"Đây thường là lỗi tham chiếu sai sau khi xóa/sắp xếp lại các điều khoản hợp đồng."
                        ),
                        side_a={
                            "label": "Điều trích dẫn trong bài",
                            "value": f"Điều {clause_num}",
                        },
                        side_b={
                            "label": "Số Điều thực tế tối đa",
                            "value": f"Điều {max_clause}",
                            "total_clauses": len(actual_clauses),
                        },
                        span=ref.span,
                        extra={
                            "referenced_clause": clause_num,
                            "max_actual_clause": max_clause,
                            "actual_clauses": actual_clauses,
                        },
                    )
                )

        return conflicts
