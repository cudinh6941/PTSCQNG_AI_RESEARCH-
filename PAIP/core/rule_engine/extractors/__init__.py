"""
Entity Extractors Package for Consistency Auditing.
"""

from .base_extractor import (
    BaseEntityExtractor,
    EntityType,
    ExtractedEntity,
    EntityMatrix,
)
from .document_code import DocumentCodeExtractor
from .money_extractor import MoneyExtractor, vietnamese_words_to_number
from .date_extractor import DateExtractor
from .duration_extractor import DurationExtractor
from .percentage_extractor import PercentageExtractor


def extract_entity_matrix(text: str) -> EntityMatrix:
    """
    Bóc tách toàn bộ các thực thể trong văn bản để tạo thành Ma trận Thực thể (Entity Matrix).

    Args:
        text: Văn bản thô cần quét.

    Returns:
        EntityMatrix chứa đầy đủ document_codes, monies, dates, percentages, clause_refs.
    """
    doc_code_extractor = DocumentCodeExtractor()
    money_extractor = MoneyExtractor()
    date_extractor = DateExtractor()
    duration_extractor = DurationExtractor()
    percentage_extractor = PercentageExtractor()

    doc_codes = doc_code_extractor.extract(text)
    monies = money_extractor.extract(text)
    dates = date_extractor.extract(text)
    durations = duration_extractor.extract(text)
    percentages = percentage_extractor.extract(text)

    return EntityMatrix(
        document_codes=doc_codes,
        monies=monies,
        dates=dates,
        durations=durations,
        percentages=percentages,
    )


__all__ = [
    "BaseEntityExtractor",
    "EntityType",
    "ExtractedEntity",
    "EntityMatrix",
    "DocumentCodeExtractor",
    "MoneyExtractor",
    "vietnamese_words_to_number",
    "DateExtractor",
    "DurationExtractor",
    "PercentageExtractor",
    "extract_entity_matrix",
]
