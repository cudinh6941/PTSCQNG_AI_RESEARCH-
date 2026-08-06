"""
Rule Engine — Glossary Rule (Level 1: Deterministic / Fast-Match).

Thuật toán quét văn bản để:
1. Bắt các biến thể viết sai (Incorrect Variants) và gợi ý sửa.
2. Nhận diện thuật ngữ chuẩn xuất hiện trong bài (Domain Entity Detection).
3. Xây dựng Whitelist & Prompt Injection context cho LLM.

Tốc độ mục tiêu: < 10ms trên văn bản 10.000 ký tự.
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from core.common.logger import logger

from ..base import (
    BaseRule,
    DetectedTerm,
    RuleResult,
    RuleSeverity,
    RuleType,
    RuleViolation,
)
from ..loaders.json_loader import GlossaryItem, GlossaryLoader

if TYPE_CHECKING:
    from ..context import RuleContext


class GlossaryRule(BaseRule):
    """
    Kiểm tra từ điển & thuật ngữ chuẩn PTSC.

    Sử dụng Compiled Regex để quét nhanh toàn bộ văn bản.
    Khi khởi tạo, tự động compile sẵn patterns vào RAM
    để đạt tốc độ so khớp tối đa.
    """

    def __init__(
        self,
        loader: GlossaryLoader,
        *,
        enabled: bool = True,
        severity: RuleSeverity = RuleSeverity.WARNING,
        max_inject_terms: int = 15,
    ):
        super().__init__(enabled=enabled, severity=severity)
        self._loader = loader
        self._max_inject_terms = max_inject_terms

        # Compiled regex patterns (build khi gọi compile())
        self._variant_patterns: list[tuple[re.Pattern, GlossaryItem]] = []
        self._standard_patterns: list[tuple[re.Pattern, GlossaryItem]] = []

    @property
    def rule_type(self) -> RuleType:
        return RuleType.GLOSSARY

    @property
    def name(self) -> str:
        return "Glossary & Terminology Rule"

    def compile(self) -> None:
        """
        Biên dịch sẵn tất cả Regex patterns từ kho từ điển.

        Gọi phương thức này sau khi loader.load() hoặc khi cần reload.
        """
        self._variant_patterns.clear()
        self._standard_patterns.clear()

        items = self._loader.get_all_terms()

        for _key, item in items.items():
            # 1. Compile patterns cho các biến thể sai
            if item.incorrect_variants:
                escaped = [re.escape(v) for v in item.incorrect_variants]
                try:
                    pattern = re.compile(
                        r"\b(" + "|".join(escaped) + r")\b",
                        re.IGNORECASE,
                    )
                    self._variant_patterns.append((pattern, item))
                except re.error as e:
                    logger.warning(f"Invalid regex for variants of '{item.term}': {e}")

            # 2. Compile patterns cho thuật ngữ chuẩn (nhận diện)
            try:
                standard_escaped = re.escape(item.standard_case or item.term)
                pattern = re.compile(
                    r"\b" + standard_escaped + r"\b",
                    re.IGNORECASE if item.standard_case.islower() else 0,
                )
                self._standard_patterns.append((pattern, item))
            except re.error as e:
                logger.warning(f"Invalid regex for standard term '{item.term}': {e}")

        logger.info(
            f"GlossaryRule compiled: {len(self._variant_patterns)} variant patterns, "
            f"{len(self._standard_patterns)} standard patterns"
        )

    def evaluate(self, context: RuleContext) -> RuleResult:
        """
        Thực thi quét từ điển trên văn bản.

        Returns:
            RuleResult chứa:
            - violations: Danh sách lỗi biến thể sai.
            - detected_terms: Thuật ngữ chuyên ngành tìm thấy.
            - whitelist_terms: Danh sách từ chuẩn cấm LLM sửa.
            - prompt_injection: Đoạn text định nghĩa thuật ngữ để bơm vào prompt.
        """
        if not self.enabled or not context.enable_glossary:
            return RuleResult()

        start_time = time.perf_counter()

        text = context.text
        violations: list[RuleViolation] = []
        detected_terms_map: dict[str, DetectedTerm] = {}
        severity = RuleSeverity.ERROR if context.strict_mode else self.default_severity

        # ── Bước 1: Quét biến thể sai ────────────────────────
        for pattern, item in self._variant_patterns:
            for match in pattern.finditer(text):
                matched_text = match.group()
                # Kiểm tra xem từ match có đúng là chuẩn rồi thì bỏ qua
                if matched_text == item.standard_case:
                    continue

                violations.append(
                    RuleViolation(
                        rule_id="GLOSSARY_INCORRECT_VARIANT",
                        rule_type=RuleType.GLOSSARY,
                        severity=severity,
                        original_text=matched_text,
                        suggested_fix=item.standard_case,
                        explanation=(
                            f"Sai quy chuẩn viết tắt/thuật ngữ. "
                            f"Cách viết đúng: '{item.standard_case}'"
                            + (f" ({item.full_name_vi})" if item.full_name_vi else "")
                            + "."
                        ),
                        position={
                            "start_char": match.start(),
                            "end_char": match.end(),
                        },
                    )
                )

                # Đồng thời ghi nhận thuật ngữ này vào detected_terms
                term_key = item.term.upper()
                if term_key not in detected_terms_map:
                    detected_terms_map[term_key] = DetectedTerm(
                        term=item.term,
                        full_name_vi=item.full_name_vi,
                        full_name_en=item.full_name_en,
                        domain=item.domain,
                        description=item.description,
                        do_not_translate=item.do_not_translate,
                    )

        # ── Bước 2: Nhận diện thuật ngữ chuẩn có trong bài ──
        for pattern, item in self._standard_patterns:
            if pattern.search(text):
                term_key = item.term.upper()
                if term_key not in detected_terms_map:
                    detected_terms_map[term_key] = DetectedTerm(
                        term=item.term,
                        full_name_vi=item.full_name_vi,
                        full_name_en=item.full_name_en,
                        domain=item.domain,
                        description=item.description,
                        do_not_translate=item.do_not_translate,
                    )

        # ── Bước 3: Xây dựng Whitelist & Prompt Injection ───
        detected_list = list(detected_terms_map.values())
        whitelist = [dt.term for dt in detected_list]

        prompt_injection = self._build_prompt_injection(detected_list)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"GlossaryRule: found {len(violations)} violations, "
            f"{len(detected_list)} terms detected, "
            f"processed in {elapsed_ms:.2f}ms"
        )

        return RuleResult(
            violations=violations,
            detected_terms=detected_list,
            whitelist_terms=whitelist,
            prompt_injection=prompt_injection,
            processing_time_ms=elapsed_ms,
        )

    def _build_prompt_injection(self, detected_terms: list[DetectedTerm]) -> str:
        """
        Tạo đoạn text chứa định nghĩa thuật ngữ chuyên ngành
        để bơm vào System Prompt cho LLM.

        Giới hạn tối đa `max_inject_terms` thuật ngữ để tránh phình token.
        """
        if not detected_terms:
            return ""

        terms_to_inject = detected_terms[: self._max_inject_terms]

        lines = [
            "THUẬT NGỮ CHUYÊN NGÀNH NỘI BỘ (ĐÃ ĐƯỢC XÁC MINH — KHÔNG ĐƯỢC SỬA, KHÔNG ĐƯỢC DỊCH SAI):"
        ]
        for dt in terms_to_inject:
            parts = [f"- {dt.term}"]
            if dt.full_name_vi:
                parts.append(f": {dt.full_name_vi}")
            if dt.full_name_en:
                parts.append(f" ({dt.full_name_en})")
            if dt.description:
                parts.append(f" — {dt.description}")
            lines.append("".join(parts))

        return "\n".join(lines)
