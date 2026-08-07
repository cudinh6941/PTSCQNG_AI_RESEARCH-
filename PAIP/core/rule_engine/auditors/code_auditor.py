"""
CA-001: Document Code Consistency Auditor.

Kiểm tra sự bất nhất của số hiệu văn bản giữa Header, Nội dung và Phụ lục đính kèm.
"""

from __future__ import annotations

from collections import defaultdict
import re

from ..base import RuleSeverity
from ..extractors.base_extractor import EntityMatrix, ExtractedEntity
from .base_auditor import AuditConflict, BaseAuditor


class DocumentCodeAuditor(BaseAuditor):
    """
    Quy tắc CA-001: Kiểm tra tính nhất quán của số hiệu văn bản.

    Ví dụ phát hiện:
    - Header trang 1 ghi: '43/TMCG-TKE'
    - Phụ lục trang 2 ghi: '46/TMCG-TKE' (do copy paste từ văn bản cũ)
    """

    @property
    def rule_id(self) -> str:
        return "CA-001"

    @property
    def rule_name(self) -> str:
        return "Document Code Consistency"

    def audit(self, matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
        codes = matrix.document_codes
        if len(codes) < 2:
            return []

        conflicts: list[AuditConflict] = []

        # Gom nhóm theo suffix (cơ quan ban hành / loại văn bản)
        # VD suffix: "TMCG-TKE", "HĐ-PTSC", "QĐ-PTSC"
        suffix_groups: dict[str, list[ExtractedEntity]] = defaultdict(list)
        for code in codes:
            suffix = code.extra.get("doc_suffix", "")
            if suffix and len(suffix) >= 3:
                suffix_groups[suffix.upper()].append(code)

        for suffix, group in suffix_groups.items():
            if len(group) < 2:
                continue

            # Kiểm tra xem có các giá trị mã khác nhau trong cùng 1 nhóm suffix không
            unique_codes = {e.normalized_value: e for e in group}
            if len(unique_codes) > 1:
                # Tìm mã chính (ưu tiên mã ở header hoặc xuất hiện đầu tiên)
                primary = next((e for e in group if e.section == "header"), group[0])

                for other in group:
                    if other.normalized_value != primary.normalized_value:
                        # Kiểm tra xem có phải ngữ cảnh trích dẫn có chủ đích (thay thế, căn cứ, bổ sung)
                        ctx = other.context_snippet.lower()
                        if any(kw in ctx for kw in ("thay thế cho", "căn cứ theo số", "hủy bỏ số", "sửa đổi số")):
                            continue

                        conflicts.append(
                            AuditConflict(
                                rule_id=self.rule_id,
                                rule_name=self.rule_name,
                                severity=RuleSeverity.ERROR,
                                description=(
                                    f"Số hiệu văn bản bất nhất: {primary.section.upper()} ghi '{primary.normalized_value}' "
                                    f"nhưng {other.section.upper()} ghi '{other.normalized_value}'"
                                ),
                                original_text=other.raw_text,
                                suggested_fix=primary.normalized_value,
                                explanation=(
                                    f"Phát hiện cùng loại văn bản (hậu tố /{suffix}) nhưng có 2 số hiệu khác nhau. "
                                    f"Văn bản chính có số '{primary.normalized_value}', trong khi đoạn này ghi '{other.normalized_value}'. "
                                    f"Đây thường là lỗi sao chép từ hợp đồng/công văn mẫu cũ."
                                ),
                                side_a={
                                    "label": f"Vế chính ({primary.section.title()})",
                                    "value": primary.normalized_value,
                                    "location": f"Dòng {primary.line_number}" if primary.line_number else "Phần đầu văn bản",
                                },
                                side_b={
                                    "label": f"Vế xung đột ({other.section.title()})",
                                    "value": other.normalized_value,
                                    "location": f"Dòng {other.line_number}" if other.line_number else "Nội dung/Phụ lục",
                                },
                                span=other.span,
                                extra={
                                    "primary_code": primary.normalized_value,
                                    "conflict_code": other.normalized_value,
                                    "suffix": suffix,
                                },
                            )
                        )

        return conflicts
