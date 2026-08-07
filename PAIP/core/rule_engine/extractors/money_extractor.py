"""
Money Extractor & Vietnamese Words-to-Number Parser.

Bóc tách số tiền bằng số, số tiền bằng chữ và hỗ trợ chuyển đổi số tiền
tiếng Việt thành dạng số để đối soát chéo (CA-002).
"""

from __future__ import annotations

import re
from typing import Any

from .base_extractor import BaseEntityExtractor, EntityType, ExtractedEntity


# ── BỘ TỪ ĐIỂN CHỮ SỐ TIẾNG VIỆT ────────────────────────────

_DIGIT_WORDS: dict[str, int] = {
    "không": 0,
    "một": 1,
    "mốt": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "tư": 4,
    "năm": 5,
    "lăm": 5,
    "sáu": 6,
    "bảy": 7,
    "bẩy": 7,
    "tám": 8,
    "chín": 9,
}

_SPECIAL_WORDS = {"lẻ", "linh", "mươi", "mười", "trăm", "nghìn", "ngàn", "triệu", "tỷ", "tỉ"}


def parse_vietnamese_sub_thousand(tokens: list[str]) -> int:
    """Chuyển đổi một cụm từ dưới 1000 (VD: 'hai trăm năm mươi ba' -> 253)."""
    if not tokens:
        return 0

    total = 0
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok in _DIGIT_WORDS:
            val = _DIGIT_WORDS[tok]
            # Xem từ tiếp theo
            if i + 1 < n and tokens[i + 1] == "trăm":
                total += val * 100
                i += 2
                continue
            elif i + 1 < n and tokens[i + 1] in ("mươi", "mười"):
                total += val * 10
                i += 2
                continue
            else:
                total += val
                i += 1
                continue

        elif tok == "mười":
            # Ví dụ: mười lăm -> 15, mười -> 10
            if i + 1 < n and tokens[i + 1] in _DIGIT_WORDS:
                total += 10 + _DIGIT_WORDS[tokens[i + 1]]
                i += 2
            else:
                total += 10
                i += 1
            continue

        elif tok in ("lẻ", "linh"):
            # Ví dụ: lẻ năm -> 5
            i += 1
            if i < n and tokens[i] in _DIGIT_WORDS:
                total += _DIGIT_WORDS[tokens[i]]
                i += 1
            continue

        elif tok == "mươi":
            i += 1
            continue
        elif tok == "trăm":
            i += 1
            continue
        else:
            i += 1

    return total


def vietnamese_words_to_number(text: str) -> int | None:
    """
    Chuyển đổi chuỗi số tiền bằng chữ tiếng Việt thành số nguyên (integer).

    Ví dụ:
    - 'Một trăm năm mươi triệu đồng' -> 150000000
    - 'Hai tỷ ba trăm bốn mươi lăm triệu năm trăm nghìn đồng' -> 2345500000
    - 'Mười lăm triệu năm trăm ngàn đồng' -> 15500000
    - 'Năm mươi nghìn đồng' -> 50000

    Returns:
        int nếu parse thành công, None nếu không nhận diện được.
    """
    if not text:
        return None

    # Làm sạch văn bản
    cleaned = text.lower()
    cleaned = re.sub(r"[,\.\(\)\–\-]", " ", cleaned)
    cleaned = re.sub(r"\b(bằng chữ|đồng|chẵn|vnđ|vnd|usd|dollars?|việt nam đồng)\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    tokens = cleaned.split()
    if not tokens:
        return None

    # Kiểm tra xem có chứa ít nhất 1 từ chỉ số không
    has_valid_word = any(tok in _DIGIT_WORDS or tok in _SPECIAL_WORDS for tok in tokens)
    if not has_valid_word:
        return None

    total = 0
    cur_chunk: list[str] = []

    for tok in tokens:
        if tok in ("tỷ", "tỉ"):
            chunk_val = parse_vietnamese_sub_thousand(cur_chunk)
            if chunk_val == 0 and not cur_chunk:
                chunk_val = 1
            total += chunk_val * 1_000_000_000
            cur_chunk = []
        elif tok == "triệu":
            chunk_val = parse_vietnamese_sub_thousand(cur_chunk)
            if chunk_val == 0 and not cur_chunk:
                chunk_val = 1
            total += chunk_val * 1_000_000
            cur_chunk = []
        elif tok in ("nghìn", "ngàn"):
            chunk_val = parse_vietnamese_sub_thousand(cur_chunk)
            if chunk_val == 0 and not cur_chunk:
                chunk_val = 1
            total += chunk_val * 1_000
            cur_chunk = []
        else:
            cur_chunk.append(tok)

    if cur_chunk:
        total += parse_vietnamese_sub_thousand(cur_chunk)

    return total if total > 0 else None


class MoneyExtractor(BaseEntityExtractor):
    """Bóc tách các đại lượng tiền tệ (bằng số, bằng chữ và cặp tiền tệ đối soát)."""

    # Pattern tiền bằng số: 150.000.000 VNĐ, 50,000 USD, 150.000.000 đ
    _NUMERIC_MONEY_PATTERN = re.compile(
        r"(\b\d{1,3}(?:[.,]\d{3})+|\b\d+)\s*(VNĐ|VND|đồng|đ|USD|\$|EUR)\b",
        re.IGNORECASE | re.UNICODE,
    )

    # Pattern tiền bằng chữ
    _WORDS_MONEY_PATTERN = re.compile(
        r"(?:(?:bằng chữ|Bằng chữ)[:\s]*|\()?"
        r"((?:[Mm]ột|[Hh]ai|[Bb]a|[Bb]ốn|[Nn]ăm|[Ss]áu|[Bb]ảy|[Bb]ẩy|[Tt]ám|[Cc]hín|[Mm]ười|[Mm]ươi|[Tt]răm|[Nn]ghìn|[Nn]gàn|[Tt]riệu|[Tt]ỷ|[Tt]ỉ|[Ll]ẻ|[Ll]inh|[Mm]ốt|[Ll]ăm|[Tt]ư)[\s,]+)+[đĐ]ồng(?:\s*chẵn)?(?:\s*\))?",
        re.UNICODE,
    )

    @property
    def entity_type(self) -> EntityType:
        return EntityType.MONEY

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text:
            return []

        results: list[ExtractedEntity] = []
        total_len = len(text)

        # 1. Bóc tách số tiền bằng số
        for match in self._NUMERIC_MONEY_PATTERN.finditer(text):
            raw_num_str = match.group(1).strip()
            currency = match.group(2).strip().upper()
            start_char, end_char = match.span()

            # Chuẩn hóa giá trị số
            clean_num = raw_num_str.replace(".", "").replace(",", "")
            try:
                numeric_val = float(clean_num)
            except ValueError:
                continue

            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.MONEY,
                    raw_text=match.group(0).strip(),
                    normalized_value=numeric_val,
                    span=(start_char, end_char),
                    context_snippet=snippet,
                    section="body",
                    extra={
                        "form": "numeric",
                        "currency": currency,
                        "raw_number": raw_num_str,
                    },
                )
            )

        # 2. Bóc tách số tiền bằng chữ
        for match in self._WORDS_MONEY_PATTERN.finditer(text):
            raw_words = match.group(0).strip()
            start_char, end_char = match.span()

            parsed_val = vietnamese_words_to_number(raw_words)
            if parsed_val is None:
                continue

            snippet_start = max(0, start_char - 40)
            snippet_end = min(total_len, end_char + 40)
            snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

            results.append(
                ExtractedEntity(
                    entity_type=EntityType.MONEY,
                    raw_text=raw_words,
                    normalized_value=float(parsed_val),
                    span=(start_char, end_char),
                    context_snippet=snippet,
                    section="body",
                    extra={
                        "form": "words",
                        "currency": "VND",
                        "parsed_amount": parsed_val,
                    },
                )
            )

        return results
