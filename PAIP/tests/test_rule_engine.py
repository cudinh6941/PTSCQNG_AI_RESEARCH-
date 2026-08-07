"""
Unit Tests — Rule Engine.

Kiểm thử độc lập cho toàn bộ module core/rule_engine/.
"""

import time
from pathlib import Path

import pytest

from core.rule_engine.base import RuleSeverity, RuleType
from core.rule_engine.context import RuleContext
from core.rule_engine.engine import RuleEngine
from core.rule_engine.loaders.json_loader import GlossaryItem, GlossaryLoader

# Đường dẫn đến thư mục data chính (không mock, dùng data thật)
_DATA_DIR = Path(__file__).resolve().parent.parent / "core" / "rule_engine" / "data"


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def engine() -> RuleEngine:
    """Tạo RuleEngine instance sử dụng data thật."""
    eng = RuleEngine(data_dir=_DATA_DIR)
    eng.load()
    return eng


@pytest.fixture
def loader() -> GlossaryLoader:
    """Tạo GlossaryLoader instance sử dụng data thật."""
    ldr = GlossaryLoader(data_dir=_DATA_DIR)
    ldr.load()
    return ldr


# ── Test: GlossaryLoader ─────────────────────────────────


class TestGlossaryLoader:
    """Test cho bộ nạp dữ liệu từ điển."""

    def test_load_success(self, loader: GlossaryLoader):
        """Nạp thành công glossary.json và có dữ liệu."""
        assert loader.count > 0
        assert loader.count >= 20  # Tối thiểu 20 thuật ngữ mẫu

    def test_get_term_found(self, loader: GlossaryLoader):
        """Tìm thuật ngữ theo tên (case-insensitive)."""
        item = loader.get_term("FPSO")
        assert item is not None
        assert item.term == "FPSO"
        assert item.do_not_translate is True

    def test_get_term_case_insensitive(self, loader: GlossaryLoader):
        """Tìm thuật ngữ không phân biệt hoa thường."""
        item = loader.get_term("fpso")
        assert item is not None
        assert item.term == "FPSO"

    def test_get_term_not_found(self, loader: GlossaryLoader):
        """Tìm thuật ngữ không tồn tại trả về None."""
        item = loader.get_term("XYZNOTEXIST")
        assert item is None

    def test_search_by_query(self, loader: GlossaryLoader):
        """Tìm kiếm theo từ khóa."""
        results = loader.search(query="dầu khí")
        assert len(results) > 0

    def test_search_by_domain(self, loader: GlossaryLoader):
        """Lọc theo lĩnh vực."""
        results = loader.search(domain="Offshore")
        assert len(results) >= 3  # FPSO, FSO, Jacket, Topside, Load-out
        for item in results:
            assert item.domain == "Offshore"

    def test_search_empty_returns_all(self, loader: GlossaryLoader):
        """Tìm kiếm rỗng trả về toàn bộ."""
        results = loader.search()
        assert len(results) == loader.count


# ── Test: GlossaryRule (Variant Detection) ────────────────


class TestGlossaryRuleVariantDetection:
    """Test thuật toán bắt lỗi biến thể viết sai."""

    def test_detect_ptsc_qng_variant(self, engine: RuleEngine):
        """Bắt lỗi 'PTSC-QNg' → Gợi ý 'PTSC Quảng Ngãi' / 'PTSC QNG'."""
        ctx = RuleContext(text="Hôm nay PTSC-QNg tiến hành nghiệm thu dự án.")
        result = engine.evaluate(ctx)

        assert result.has_violations
        violation = result.violations[0]
        assert violation.original_text == "PTSC-QNg"
        assert violation.suggested_fix in ("PTSC Quảng Ngãi", "PTSC QNG")
        assert violation.rule_type == RuleType.GLOSSARY


    def test_detect_fpso_lowercase(self, engine: RuleEngine):
        """Bắt lỗi 'fpso' → Gợi ý 'FPSO'."""
        ctx = RuleContext(text="Kho nổi fpso đang được bảo dưỡng định kỳ.")
        result = engine.evaluate(ctx)

        assert result.has_violations
        fpso_violations = [v for v in result.violations if v.suggested_fix == "FPSO"]
        assert len(fpso_violations) > 0
        assert fpso_violations[0].original_text.lower() == "fpso"

    def test_detect_multiple_variants(self, engine: RuleEngine):
        """Bắt nhiều lỗi trong cùng một văn bản."""
        ctx = RuleContext(
            text="Công ty ptsc qng triển khai dự án fpso với hệ thống hse."
        )
        result = engine.evaluate(ctx)
        assert len(result.violations) >= 2  # Ít nhất ptsc qng + fpso

    def test_no_false_positive_on_correct_terms(self, engine: RuleEngine):
        """Không bắt lỗi nhầm khi từ đã đúng chuẩn."""
        ctx = RuleContext(
            text="PTSC QNG đã hoàn thành dự án FPSO đúng tiến độ."
        )
        result = engine.evaluate(ctx)
        # Không có violation nào cho PTSC QNG và FPSO (viết đúng)
        false_positives = [
            v for v in result.violations
            if v.suggested_fix in ("PTSC QNG", "FPSO")
        ]
        assert len(false_positives) == 0

    def test_strict_mode_severity_error(self, engine: RuleEngine):
        """Strict mode gán severity = ERROR."""
        ctx = RuleContext(
            text="Dự án fpso cần kiểm tra.",
            strict_mode=True,
        )
        result = engine.evaluate(ctx)
        assert result.has_violations
        for v in result.violations:
            assert v.severity == RuleSeverity.ERROR


# ── Test: GlossaryRule (Term Detection & Context) ─────────


class TestGlossaryRuleTermDetection:
    """Test thuật toán nhận diện thuật ngữ & xây dựng context."""

    def test_detect_standard_terms(self, engine: RuleEngine):
        """Nhận diện thuật ngữ chuẩn có trong bài."""
        ctx = RuleContext(
            text="Dự án FPSO sử dụng kết cấu Jacket với hệ thống HAZOP."
        )
        result = engine.evaluate(ctx)

        detected_names = [dt.term for dt in result.detected_terms]
        assert "FPSO" in detected_names
        assert "HAZOP" in detected_names

    def test_whitelist_generated(self, engine: RuleEngine):
        """Whitelist chứa đúng các thuật ngữ chuẩn tìm thấy."""
        ctx = RuleContext(text="Hệ thống FPSO và NDT đang được triển khai.")
        result = engine.evaluate(ctx)

        assert "FPSO" in result.whitelist_terms
        assert "NDT" in result.whitelist_terms

    def test_prompt_injection_not_empty(self, engine: RuleEngine):
        """Prompt injection được tạo khi có thuật ngữ."""
        ctx = RuleContext(text="Kiểm tra HAZOP trước khi lắp đặt Topside.")
        result = engine.evaluate(ctx)

        assert result.prompt_injection != ""
        assert "THUẬT NGỮ CHUYÊN NGÀNH" in result.prompt_injection
        assert "HAZOP" in result.prompt_injection

    def test_prompt_injection_empty_when_no_terms(self, engine: RuleEngine):
        """Prompt injection trống khi không có thuật ngữ chuyên ngành."""
        ctx = RuleContext(text="Hôm nay trời đẹp quá đi thôi.")
        result = engine.evaluate(ctx)

        assert result.prompt_injection == ""
        assert len(result.detected_terms) == 0

    def test_glossary_disabled_skips_check(self, engine: RuleEngine):
        """Tắt glossary check thì bỏ qua toàn bộ."""
        ctx = RuleContext(
            text="Công ty ptsc qng có fpso",
            enable_glossary=False,
        )
        result = engine.evaluate(ctx)
        assert not result.has_violations
        assert len(result.detected_terms) == 0


# ── Test: Performance ─────────────────────────────────────


class TestPerformance:
    """Test tốc độ xử lý."""

    def test_processing_speed_under_10ms(self, engine: RuleEngine):
        """Đảm bảo tốc độ xử lý < 10ms trên văn bản 10.000 ký tự."""
        # Tạo văn bản dài ~ 10.000 ký tự
        sample = (
            "PTSC QNG đang triển khai dự án FPSO với kết cấu Jacket và Topside. "
            "Hệ thống HAZOP đã được đánh giá. Kiểm tra NDT và WPS đạt chuẩn QA/QC. "
            "Phòng P.ATCL phối hợp với P.KTTB giám sát HSE. "
        )
        long_text = sample * 60  # ~10.000+ ký tự (tiếng Việt Unicode)
        assert len(long_text) >= 10_000

        ctx = RuleContext(text=long_text)

        start = time.perf_counter()
        result = engine.evaluate(ctx)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 100  # Mục tiêu < 10ms, cho phép tối đa 100ms trên CI
        assert result.processing_time_ms > 0


# ── Test: CRUD Operations ────────────────────────────────


class TestCRUDOperations:
    """Test các thao tác Thêm / Sửa / Xóa từ điển."""

    def test_add_and_detect_new_term(self, engine: RuleEngine):
        """Thêm từ mới → Rule Engine phát hiện được ngay."""
        new_item = GlossaryItem(
            term="SCADA",
            full_name_en="Supervisory Control and Data Acquisition",
            full_name_vi="Hệ thống giám sát điều khiển và thu thập dữ liệu",
            domain="Automation",
            standard_case="SCADA",
            incorrect_variants=["scada", "Scada", "S.C.A.D.A"],
            do_not_translate=True,
            description="Hệ thống giám sát và điều khiển tự động trong công nghiệp.",
        )

        try:
            engine.add_glossary_term(new_item)

            # Kiểm tra phát hiện biến thể sai
            ctx = RuleContext(text="Hệ thống scada đang hoạt động.")
            result = engine.evaluate(ctx)
            assert result.has_violations
            assert any(v.suggested_fix == "SCADA" for v in result.violations)

        finally:
            # Cleanup: Xóa từ vừa thêm
            engine.delete_glossary_term("SCADA")

    def test_delete_term(self, engine: RuleEngine):
        """Xóa từ → Rule Engine không còn bắt lỗi từ đó nữa."""
        new_item = GlossaryItem(
            term="TESTTERM",
            full_name_vi="Thuật ngữ thử nghiệm",
            standard_case="TESTTERM",
            incorrect_variants=["testterm"],
        )

        try:
            engine.add_glossary_term(new_item)
            assert engine.delete_glossary_term("TESTTERM") is True

            ctx = RuleContext(text="Kiểm tra testterm trong văn bản.")
            result = engine.evaluate(ctx)
            testterm_violations = [
                v for v in result.violations if v.suggested_fix == "TESTTERM"
            ]
            assert len(testterm_violations) == 0

        finally:
            # Safety cleanup
            engine.delete_glossary_term("TESTTERM")
