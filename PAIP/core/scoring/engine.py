"""
PAIP — Quality Scoring Engine (Bảng Chấm Điểm Chất Lượng Văn Bản 4 Trụ Cột)
Calculates transparent and weighted composite scores for Vietnamese enterprise documents.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PillarScore(BaseModel):
    """Score metric for a single quality pillar."""
    name: str
    score: float = Field(ge=0.0, le=10.0)
    weight: float = Field(default=0.25, ge=0.0, le=1.0)
    issue_count: int = Field(default=0, ge=0)
    status: str = Field(default="pass")  # 'pass' | 'warning' | 'danger'
    details: Optional[str] = None


class QualityScoreBreakdown(BaseModel):
    """Complete 4-pillar quality scorecard."""
    overall_score: float = Field(ge=0.0, le=10.0)
    rating: str  # 'EXCELLENT' | 'ACCEPTABLE' | 'NEEDS_REVISION'
    rating_label: str
    is_publish_ready: bool
    pillars: Dict[str, PillarScore]
    summary_recommendation: str


class QualityScoringEngine:
    """
    Evaluates documents across 4 core pillars:
    1. Spelling & Grammar (Chính tả & Ngữ pháp)
    2. Format Compliance Decree 30 (Thể thức Nghị định 30/2020/NĐ-CP)
    3. PTSC Brand & Glossary (Thuật ngữ & Quy chuẩn PTSC)
    4. Information Consistency (Tính nhất quán & Số liệu)
    """

    def __init__(
        self,
        weight_spelling: float = 0.25,
        weight_format: float = 0.25,
        weight_glossary: float = 0.25,
        weight_consistency: float = 0.25,
    ):
        self.weights = {
            "spelling": weight_spelling,
            "format": weight_format,
            "glossary": weight_glossary,
            "consistency": weight_consistency,
        }

    def evaluate(
        self,
        errors: List[Any],
        format_report: Optional[Dict[str, Any]] = None,
        consistency_conflicts: Optional[List[Any]] = None,
    ) -> QualityScoreBreakdown:
        """
        Calculates 4 pillar scores and a composite overall quality score.
        """
        # 1. Evaluate Spelling & Grammar
        spelling_errors = [e for e in errors if self._get_error_category(e) in ["spelling", "grammar", "punctuation", "word_choice"]]
        spelling_score, spelling_issues = self._calc_spelling_score(spelling_errors)

        # 2. Evaluate Format (Decree 30)
        format_score, format_issues = self._calc_format_score(format_report)

        # 3. Evaluate PTSC Glossary
        glossary_errors = [e for e in errors if self._get_error_category(e) in ["glossary", "terminology", "branding"]]
        glossary_score, glossary_issues = self._calc_glossary_score(glossary_errors)

        # 4. Evaluate Consistency & Numbers
        consistency_errors = [e for e in errors if self._get_error_category(e) in ["consistency", "numbers", "legal"]]
        if consistency_conflicts:
            consistency_errors.extend(consistency_conflicts)
        consistency_score, consistency_issues = self._calc_consistency_score(consistency_errors)

        # Compute Weighted Overall Score
        overall = (
            spelling_score * self.weights["spelling"]
            + format_score * self.weights["format"]
            + glossary_score * self.weights["glossary"]
            + consistency_score * self.weights["consistency"]
        )
        overall = round(max(1.0, min(10.0, overall)), 1)

        # Classification
        if overall >= 9.0:
            rating = "EXCELLENT"
            rating_label = "Xuất sắc — Đủ điều kiện phát hành"
            is_publish_ready = True
        elif overall >= 7.0:
            rating = "ACCEPTABLE"
            rating_label = "Đạt chuẩn — Cần hiệu đính các điểm cảnh báo"
            is_publish_ready = False
        else:
            rating = "NEEDS_REVISION"
            rating_label = "Chưa đạt chuẩn — Cần soát xét lại trước khi trình ký"
            is_publish_ready = False

        # Build Pillars
        pillars = {
            "spelling": PillarScore(
                name="Chính tả & Ngữ pháp",
                score=round(spelling_score, 1),
                weight=self.weights["spelling"],
                issue_count=spelling_issues,
                status="pass" if spelling_score >= 9.0 else ("warning" if spelling_score >= 7.0 else "danger"),
                details=f"{spelling_issues} điểm cần sửa" if spelling_issues > 0 else "Không phát hiện lỗi",
            ),
            "format": PillarScore(
                name="Thể thức (NĐ 30/2020/NĐ-CP)",
                score=round(format_score, 1),
                weight=self.weights["format"],
                issue_count=format_issues,
                status="pass" if format_score >= 9.0 else ("warning" if format_score >= 7.0 else "danger"),
                details=f"{format_issues} điểm vi phạm" if format_issues > 0 else "Chuẩn thể thức A4",
            ),
            "glossary": PillarScore(
                name="Thuật ngữ PTSC",
                score=round(glossary_score, 1),
                weight=self.weights["glossary"],
                issue_count=glossary_issues,
                status="pass" if glossary_score >= 9.0 else ("warning" if glossary_score >= 7.0 else "danger"),
                details=f"{glossary_issues} lỗi từ điển/nhận diện" if glossary_issues > 0 else "Chuẩn nhận diện thương hiệu",
            ),
            "consistency": PillarScore(
                name="Nhất quán & Số liệu",
                score=round(consistency_score, 1),
                weight=self.weights["consistency"],
                issue_count=consistency_issues,
                status="pass" if consistency_score >= 9.0 else ("warning" if consistency_score >= 7.0 else "danger"),
                details=f"{consistency_issues} điểm bất nhất" if consistency_issues > 0 else "Số liệu & số hiệu nhất quán",
            ),
        }

        # Build Recommendation Summary
        summary = self._build_recommendation(overall, pillars)

        return QualityScoreBreakdown(
            overall_score=overall,
            rating=rating,
            rating_label=rating_label,
            is_publish_ready=is_publish_ready,
            pillars=pillars,
            summary_recommendation=summary,
        )

    def _get_error_category(self, error: Any) -> str:
        """Extract category or error_type from error dictionary or Pydantic model."""
        if hasattr(error, "type"):
            val = getattr(error, "type")
            return getattr(val, "value", str(val)).lower()
        if hasattr(error, "error_type"):
            val = getattr(error, "error_type")
            return getattr(val, "value", str(val)).lower()
        if isinstance(error, dict):
            return str(error.get("type", error.get("error_type", error.get("category", "spelling")))).lower()
        return "spelling"

    def _get_severity(self, error: Any) -> str:
        """Extract severity."""
        if hasattr(error, "severity"):
            return str(getattr(error, "severity")).upper()
        if isinstance(error, dict):
            return str(error.get("severity", "MEDIUM")).upper()
        return "MEDIUM"

    def _calc_spelling_score(self, errors: List[Any]) -> tuple[float, int]:
        """Calculates spelling & grammar score (0.0 - 10.0)."""
        score = 10.0
        for err in errors:
            sev = self._get_severity(err)
            if sev == "HIGH":
                score -= 0.5
            elif sev == "LOW":
                score -= 0.15
            else:
                score -= 0.3
        return max(0.0, score), len(errors)

    def _calc_format_score(self, format_report: Optional[Dict[str, Any]]) -> tuple[float, int]:
        """Calculates format score based on Decree 30 audit."""
        if not format_report:
            return 10.0, 0

        score = 10.0
        issues = 0

        # Margin compliance
        margins = format_report.get("margins", {})
        if isinstance(margins, dict) and margins.get("is_compliant") is False:
            score -= 2.5
            issues += 1

        # Font family compliance
        font_info = format_report.get("dominant_font", {})
        if isinstance(font_info, dict) and font_info.get("name"):
            font_name = font_info.get("name", "").lower()
            if "times" not in font_name and "vn" not in font_name:
                score -= 2.0
                issues += 1

        # Alignment compliance (justified)
        align_info = format_report.get("dominant_alignment", {})
        if isinstance(align_info, dict):
            name = align_info.get("name", "").lower()
            if "justif" not in name and "both" not in name:
                score -= 1.5
                issues += 1

        return max(0.0, score), issues

    def _calc_glossary_score(self, errors: List[Any]) -> tuple[float, int]:
        """Calculates glossary score (0.0 - 10.0)."""
        score = 10.0
        for err in errors:
            sev = self._get_severity(err)
            if sev == "HIGH":
                score -= 1.5
            else:
                score -= 1.0
        return max(0.0, score), len(errors)

    def _calc_consistency_score(self, errors: List[Any]) -> tuple[float, int]:
        """Calculates consistency score (0.0 - 10.0)."""
        score = 10.0
        for _ in errors:
            score -= 2.0  # Inconsistencies are severe
        return max(0.0, score), len(errors)

    def _build_recommendation(self, overall: float, pillars: Dict[str, PillarScore]) -> str:
        """Generates actionable feedback for executive review."""
        if overall >= 9.5:
            return "Văn bản hoàn hảo, tuân thủ chặt chẽ thể thức Nghị định 30 và quy chuẩn thuật ngữ PTSC."
        if overall >= 9.0:
            return "Văn bản đạt chất lượng xuất sắc, đủ điều kiện trình ký phê duyệt."
        
        tips = []
        if pillars["format"].score < 8.5:
            tips.append("chuẩn hóa căn lề & font chữ theo NĐ 30")
        if pillars["glossary"].score < 8.5:
            tips.append("sửa đúng quy chuẩn tên công ty và thuật ngữ PTSC")
        if pillars["consistency"].score < 8.5:
            tips.append("đối soát lại số hiệu văn bản và số tiền số/chữ")
        if pillars["spelling"].score < 8.5:
            tips.append("sửa các lỗi chính tả được phát hiện")

        if tips:
            return f"Khuyến nghị: {', '.join(tips)} trước khi phát hành chính thức."
        return "Cần rà soát và hiệu đính các điểm cảnh báo trước khi phát hành."


# Singleton Instance
quality_scoring_engine = QualityScoringEngine()
