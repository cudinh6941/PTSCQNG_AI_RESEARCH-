"""
Auditors Package for Cross-Consistency Auditing.
"""

from .base_auditor import AuditConflict, BaseAuditor
from .code_auditor import DocumentCodeAuditor
from .money_auditor import MoneyAuditor
from .timeline_auditor import TimelineAuditor
from .percentage_auditor import PercentageAuditor
from .clause_auditor import ClauseAuditor
from ..extractors.base_extractor import EntityMatrix


def run_cross_audit(matrix: EntityMatrix, full_text: str = "") -> list[AuditConflict]:
    """
    Chạy toàn bộ các bộ đối soát chéo (Auditors) trên Ma trận Thực thể.

    Args:
        matrix: EntityMatrix đã bóc tách.
        full_text: Văn bản thô đầy đủ.

    Returns:
        Danh sách tất cả các xung đột phát hiện được.
    """
    auditors: list[BaseAuditor] = [
        DocumentCodeAuditor(),
        MoneyAuditor(),
        TimelineAuditor(),
        PercentageAuditor(),
        ClauseAuditor(),
    ]

    all_conflicts: list[AuditConflict] = []
    for auditor in auditors:
        try:
            conflicts = auditor.audit(matrix, full_text)
            all_conflicts.extend(conflicts)
        except Exception as e:
            # Phòng ngừa lỗi unhandled exception trong auditor làm gián đoạn pipeline
            from core.common.logger import logger
            logger.warning(f"Auditor {auditor.rule_id} error: {e}")

    return all_conflicts


__all__ = [
    "AuditConflict",
    "BaseAuditor",
    "DocumentCodeAuditor",
    "MoneyAuditor",
    "TimelineAuditor",
    "PercentageAuditor",
    "ClauseAuditor",
    "run_cross_audit",
]
