"""
Unit & Integration Tests for Consistency Check Engine (Phase 2).
"""

import pytest
from core.rule_engine.extractors.document_code import DocumentCodeExtractor
from core.rule_engine.extractors.money_extractor import (
    MoneyExtractor,
    vietnamese_words_to_number,
)
from core.rule_engine.extractors.date_extractor import DateExtractor
from core.rule_engine.extractors.percentage_extractor import PercentageExtractor
from core.rule_engine.extractors.clause_ref_extractor import ClauseRefExtractor
from core.rule_engine.extractors import extract_entity_matrix

from core.rule_engine.auditors.code_auditor import DocumentCodeAuditor
from core.rule_engine.auditors.money_auditor import MoneyAuditor
from core.rule_engine.auditors.timeline_auditor import TimelineAuditor
from core.rule_engine.auditors.percentage_auditor import PercentageAuditor
from core.rule_engine.auditors.clause_auditor import ClauseAuditor
from core.rule_engine.auditors import run_cross_audit

from core.rule_engine.rules.consistency_rule import ConsistencyRule
from core.rule_engine.context import RuleContext
from core.rule_engine.engine import RuleEngine


class TestVietnameseWordsToNumber:
    """Kiểm tra parser chuyển đổi chữ số tiếng Việt sang số nguyên."""

    def test_basic_numbers(self):
        assert vietnamese_words_to_number("Một trăm năm mươi triệu đồng") == 150_000_000
        assert vietnamese_words_to_number("Hai tỷ ba trăm triệu đồng") == 2_300_000_000
        assert vietnamese_words_to_number("Mười lăm triệu năm trăm nghìn đồng") == 15_500_000
        assert vietnamese_words_to_number("Năm mươi triệu đồng chẵn") == 50_000_000

    def test_complex_and_alternative_words(self):
        # 'ngàn' thay cho 'nghìn', 'tỉ' thay cho 'tỷ', 'lăm', 'tư'
        assert vietnamese_words_to_number("Một trăm hai mươi tư triệu năm trăm ngàn đồng") == 124_500_000
        assert vietnamese_words_to_number("Ba tỉ năm mươi triệu đồng") == 3_050_000_000
        assert vietnamese_words_to_number("Mười lăm triệu đồng") == 15_000_000

    def test_invalid_input(self):
        assert vietnamese_words_to_number("") is None
        assert vietnamese_words_to_number("Không có số nào ở đây") is None


class TestExtractors:
    """Kiểm tra các bộ bóc tách thực thể."""

    def test_document_code_extractor(self):
        text = "Số: 43/TMCG-TKE ngày 06/08/2026. Phụ lục đính kèm số 46/TMCG-TKE."
        extractor = DocumentCodeExtractor()
        entities = extractor.extract(text)
        assert len(entities) >= 2
        assert entities[0].normalized_value == "43/TMCG-TKE"
        assert entities[1].normalized_value == "46/TMCG-TKE"
        assert entities[0].section == "header"
        assert entities[1].section == "attachment"

    def test_money_extractor(self):
        text = "Tổng giá trị: 150.000.000 VNĐ (Bằng chữ: Một trăm năm mươi triệu đồng chẵn)."
        extractor = MoneyExtractor()
        entities = extractor.extract(text)
        assert len(entities) == 2
        assert entities[0].normalized_value == 150_000_000.0
        assert entities[1].normalized_value == 150_000_000.0

    def test_date_extractor(self):
        text = "Quảng Ngãi, ngày 10 tháng 08 năm 2026. Hạn nộp hồ sơ trước ngày 08/08/2026."
        extractor = DateExtractor()
        entities = extractor.extract(text)
        assert len(entities) == 2
        assert entities[0].extra["role"] == "issued_date"
        assert entities[1].extra["role"] == "deadline"

    def test_percentage_extractor(self):
        text = "Tạm ứng đợt 1: 30%, Giao hàng đợt 2: 50%, Nghiệm thu đợt 3: 30%."
        extractor = PercentageExtractor()
        entities = extractor.extract(text)
        assert len(entities) == 3
        assert [e.normalized_value for e in entities] == [30.0, 50.0, 30.0]

    def test_clause_ref_extractor(self):
        text = """
        Điều 1. Phạm vi công việc
        Nội dung chi tiết...
        Điều 2. Giá trị hợp đồng
        Theo quy định tại Điều 15 Hợp đồng này.
        """
        extractor = ClauseRefExtractor()
        actual = extractor.extract_actual_clauses(text)
        assert actual == [1, 2]
        refs = extractor.extract(text)
        assert len(refs) == 1
        assert refs[0].normalized_value == 15


class TestAuditors:
    """Kiểm tra các bộ đối soát chéo (Auditors)."""

    def test_ca_001_code_auditor(self):
        text = "Số: 43/TMCG-TKE\nNội dung chính...\nPhụ lục hợp đồng số: 46/TMCG-TKE"
        matrix = extract_entity_matrix(text)
        auditor = DocumentCodeAuditor()
        conflicts = auditor.audit(matrix, text)
        assert len(conflicts) == 1
        assert conflicts[0].rule_id == "CA-001"
        assert "43/TMCG-TKE" in conflicts[0].description
        assert "46/TMCG-TKE" in conflicts[0].description

    def test_ca_002_money_mismatch(self):
        text = "Tổng giá trị: 150.000.000 VNĐ (Bằng chữ: Một trăm năm mươi hai triệu đồng)."
        matrix = extract_entity_matrix(text)
        auditor = MoneyAuditor()
        conflicts = auditor.audit(matrix, text)
        assert len(conflicts) == 1
        assert conflicts[0].rule_id == "CA-002"
        assert conflicts[0].extra["difference"] == 2_000_000.0

    def test_ca_003_timeline_paradox(self):
        text = "Quảng Ngãi, ngày 10/08/2026. Hạn nộp hồ sơ chậm nhất ngày 08/08/2026."
        matrix = extract_entity_matrix(text)
        auditor = TimelineAuditor()
        conflicts = auditor.audit(matrix, text)
        assert len(conflicts) == 1
        assert conflicts[0].rule_id == "CA-003"
        assert "muộn hơn" in conflicts[0].description

    def test_ca_005_percentage_sum(self):
        text = "Thanh toán đợt 1 tạm ứng: 30%, Thanh toán đợt 2: 50%, Thanh toán đợt 3: 30%."
        matrix = extract_entity_matrix(text)
        auditor = PercentageAuditor()
        conflicts = auditor.audit(matrix, text)
        assert len(conflicts) == 1
        assert conflicts[0].rule_id == "CA-005"
        assert conflicts[0].extra["total_percentage"] == 110.0

    def test_ca_007_ghost_clause(self):
        text = """
        Điều 1. Phạm vi
        Điều 2. Giá trị
        Căn cứ theo Điều 15 Hợp đồng này để giải quyết khiếu nại.
        """
        matrix = extract_entity_matrix(text)
        auditor = ClauseAuditor()
        conflicts = auditor.audit(matrix, text)
        assert len(conflicts) == 1
        assert conflicts[0].rule_id == "CA-007"
        assert "Điều 15" in conflicts[0].description


class TestConsistencyRuleIntegration:
    """Kiểm tra tích hợp ConsistencyRule trong RuleEngine."""

    def test_rule_engine_full_evaluation(self):
        text = """
        TỔNG CÔNG TY CỔ PHẦN DỊCH VỤ KỸ THUẬT DẦU KHÍ VIỆT NAM
        Số: 43/TMCG-TKE
        Quảng Ngãi, ngày 10/08/2026

        Căn cứ ptsc-qng và các quy định.
        Giá trị: 150.000.000 VNĐ (Bằng chữ: Một trăm năm mươi hai triệu đồng).
        Hạn nộp hồ sơ trước ngày 05/08/2026.

        Điều 1. Tạm ứng
        Thanh toán đợt 1: 30%, đợt 2: 50%, đợt 3: 30%.
        Căn cứ Điều 15 Hợp đồng này.

        Phụ lục số 46/TMCG-TKE.
        """
        engine = RuleEngine()
        context = RuleContext(text=text)
        result = engine.evaluate(context)

        # Cả Level 1 (GLOSSARY: 'ptsc-qng') và Level 2 (CONSISTENCY: CA-001, CA-002, CA-003, CA-005, CA-007)
        violation_ids = [v.rule_id for v in result.violations]
        assert "GLOSSARY_INCORRECT_VARIANT" in violation_ids
        assert "CA-001" in violation_ids
        assert "CA-002" in violation_ids
        assert "CA-003" in violation_ids
        assert "CA-005" in violation_ids
        assert "CA-007" in violation_ids
        assert len(result.violations) >= 6
        assert result.processing_time_ms < 50  # Siêu tốc < 50ms
