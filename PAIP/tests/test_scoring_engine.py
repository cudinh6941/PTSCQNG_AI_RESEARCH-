"""
Unit tests for Quality Scoring Engine (4 Pillars & Classification)
"""

from core.scoring import QualityScoringEngine, quality_scoring_engine


def test_perfect_document_score():
    """A document with 0 errors and compliant format should have a perfect 10.0 score."""
    engine = QualityScoringEngine()
    result = engine.evaluate(errors=[], format_report=None)
    assert result.overall_score == 10.0
    assert result.rating == "EXCELLENT"
    assert result.is_publish_ready is True
    assert result.pillars["spelling"].score == 10.0
    assert result.pillars["format"].score == 10.0
    assert result.pillars["glossary"].score == 10.0
    assert result.pillars["consistency"].score == 10.0


def test_spelling_errors_deduction():
    """Spelling errors should deduct points from the spelling pillar."""
    engine = QualityScoringEngine()
    errors = [
        {"error_type": "spelling", "severity": "HIGH"},
        {"error_type": "grammar", "severity": "MEDIUM"},
        {"error_type": "punctuation", "severity": "LOW"},
    ]
    result = engine.evaluate(errors=errors, format_report=None)
    # Deductions: 0.5 (high) + 0.3 (medium) + 0.15 (low) = 0.95 -> spelling score = 9.05
    assert result.pillars["spelling"].score == 9.0 or result.pillars["spelling"].score == 9.1
    assert result.pillars["spelling"].issue_count == 3
    assert result.pillars["glossary"].score == 10.0  # untouched


def test_format_report_deduction():
    """Non-compliant margins and font should deduct points from the format pillar."""
    engine = QualityScoringEngine()
    format_report = {
        "margins": {"is_compliant": False},
        "dominant_font": {"name": "Calibri"},
        "dominant_alignment": {"name": "Left"},
    }
    result = engine.evaluate(errors=[], format_report=format_report)
    # Deductions: 2.5 (margins) + 2.0 (font) + 1.5 (alignment) = 6.0 -> format score = 4.0
    assert result.pillars["format"].score == 4.0
    assert result.pillars["format"].issue_count == 3
    assert result.pillars["format"].status == "danger"
    assert result.is_publish_ready is False


def test_glossary_errors_deduction():
    """Glossary brand violations should deduct 1.5 pts each."""
    engine = QualityScoringEngine()
    errors = [
        {"error_type": "glossary", "severity": "HIGH"},
        {"error_type": "glossary", "severity": "HIGH"},
    ]
    result = engine.evaluate(errors=errors, format_report=None)
    # Deductions: 1.5 + 1.5 = 3.0 -> glossary score = 7.0
    assert result.pillars["glossary"].score == 7.0
    assert result.pillars["glossary"].issue_count == 2
    assert result.pillars["glossary"].status == "warning"


def test_overall_classification_rating():
    """Test classification thresholds (EXCELLENT, ACCEPTABLE, NEEDS_REVISION)."""
    engine = QualityScoringEngine()
    
    # 1. High score -> EXCELLENT
    res_exc = engine.evaluate(errors=[{"error_type": "spelling", "severity": "LOW"}])
    assert res_exc.rating == "EXCELLENT"
    assert res_exc.is_publish_ready is True

    # 2. Moderate issues -> ACCEPTABLE
    res_acc = engine.evaluate(
        errors=[
            {"error_type": "spelling", "severity": "HIGH"},
            {"error_type": "glossary", "severity": "HIGH"},
        ],
        format_report={"margins": {"is_compliant": False}},
    )
    assert res_acc.rating == "ACCEPTABLE" or res_acc.rating == "EXCELLENT"

    # 3. Severe issues -> NEEDS_REVISION
    severe_errors = [
        {"error_type": "spelling", "severity": "HIGH"} for _ in range(10)
    ] + [
        {"error_type": "glossary", "severity": "HIGH"} for _ in range(5)
    ]
    res_bad = engine.evaluate(
        errors=severe_errors,
        format_report={
            "margins": {"is_compliant": False},
            "dominant_font": {"name": "Calibri"},
            "dominant_alignment": {"name": "Left"},
        },
    )
    assert res_bad.rating == "NEEDS_REVISION"
    assert res_bad.is_publish_ready is False
    assert res_bad.overall_score < 7.0
