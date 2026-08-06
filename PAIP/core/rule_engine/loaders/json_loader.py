"""
Rule Engine — JSON Loader.

Đọc, validate và cung cấp dữ liệu từ điển từ file glossary.json.
Hỗ trợ CRUD (Thêm / Sửa / Xóa) và lưu lại vào file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from core.common.logger import logger

# Đường dẫn mặc định đến thư mục data
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ── Glossary Item Schema ──────────────────────────────────


class GlossaryItem(BaseModel):
    """Schema cho một mục trong kho từ điển."""

    term: str = Field(description="Thuật ngữ chuẩn (VD: 'FPSO', 'PTSC QNG')")
    full_name_en: str = Field(default="", description="Tên đầy đủ tiếng Anh")
    full_name_vi: str = Field(default="", description="Tên đầy đủ tiếng Việt")
    domain: str = Field(default="General", description="Lĩnh vực (Offshore, Corporate, HSEQ...)")
    standard_case: str = Field(default="", description="Cách viết đúng chuẩn (viết hoa / thường)")
    incorrect_variants: list[str] = Field(
        default_factory=list,
        description="Danh sách các cách viết sai thường gặp",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Các từ đồng nghĩa / cách gọi khác",
    )
    do_not_translate: bool = Field(
        default=False,
        description="True = không được dịch sang ngôn ngữ khác",
    )
    description: str = Field(default="", description="Mô tả ngắn về thuật ngữ")

    def model_post_init(self, __context: Any) -> None:
        """Tự động gán standard_case = term nếu chưa set."""
        if not self.standard_case:
            self.standard_case = self.term


# ── Glossary Loader ───────────────────────────────────────


class GlossaryLoader:
    """
    Quản lý đọc/ghi kho từ điển từ file glossary.json.

    Cung cấp:
    - load(): Nạp toàn bộ từ điển vào bộ nhớ.
    - save(): Lưu lại toàn bộ từ điển ra file.
    - add_term() / update_term() / delete_term(): CRUD operations.
    - get_all_terms(): Lấy danh sách đã nạp.
    """

    def __init__(self, data_dir: str | Path | None = None):
        self._data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self._glossary_path = self._data_dir / "glossary.json"
        self._items: dict[str, GlossaryItem] = {}  # key = term (uppercase)

    @property
    def glossary_path(self) -> Path:
        return self._glossary_path

    @property
    def count(self) -> int:
        return len(self._items)

    def load(self) -> dict[str, GlossaryItem]:
        """
        Nạp toàn bộ từ điển từ file JSON vào bộ nhớ.

        Returns:
            Dict[term_key, GlossaryItem]
        """
        if not self._glossary_path.exists():
            logger.warning(f"Glossary file not found: {self._glossary_path}. Starting with empty glossary.")
            self._items = {}
            return self._items

        try:
            raw_text = self._glossary_path.read_text(encoding="utf-8")
            raw_data: dict[str, Any] = json.loads(raw_text)

            self._items = {}
            for key, value in raw_data.items():
                try:
                    # Đảm bảo trường 'term' luôn có giá trị
                    if "term" not in value:
                        value["term"] = key
                    item = GlossaryItem(**value)
                    self._items[key.upper()] = item
                except Exception as e:
                    logger.warning(f"Skipping invalid glossary entry '{key}': {e}")

            logger.info(f"Loaded {len(self._items)} glossary terms from {self._glossary_path}")
            return self._items

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in glossary file: {e}")
            self._items = {}
            return self._items

    def save(self) -> None:
        """Lưu toàn bộ từ điển hiện tại ra file JSON (ghi đè)."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

        output: dict[str, Any] = {}
        for key, item in sorted(self._items.items()):
            output[item.term] = item.model_dump(exclude_defaults=False)

        self._glossary_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Saved {len(self._items)} glossary terms to {self._glossary_path}")

    def get_all_terms(self) -> dict[str, GlossaryItem]:
        """Trả về toàn bộ từ điển đã nạp."""
        return dict(self._items)

    def get_term(self, term: str) -> GlossaryItem | None:
        """Tìm một thuật ngữ theo key (case-insensitive)."""
        return self._items.get(term.upper())

    def add_term(self, item: GlossaryItem) -> GlossaryItem:
        """
        Thêm một thuật ngữ mới vào kho.

        Raises:
            ValueError nếu thuật ngữ đã tồn tại.
        """
        key = item.term.upper()
        if key in self._items:
            raise ValueError(f"Thuật ngữ '{item.term}' đã tồn tại trong kho từ điển.")
        self._items[key] = item
        self.save()
        logger.info(f"Added glossary term: '{item.term}'")
        return item

    def update_term(self, term: str, updates: dict[str, Any]) -> GlossaryItem:
        """
        Cập nhật một thuật ngữ đã có.

        Args:
            term: Thuật ngữ cần cập nhật.
            updates: Dict chứa các trường cần cập nhật.

        Raises:
            KeyError nếu thuật ngữ không tồn tại.
        """
        key = term.upper()
        if key not in self._items:
            raise KeyError(f"Thuật ngữ '{term}' không tồn tại trong kho từ điển.")

        existing = self._items[key]
        updated_data = existing.model_dump()
        updated_data.update(updates)
        self._items[key] = GlossaryItem(**updated_data)
        self.save()
        logger.info(f"Updated glossary term: '{term}'")
        return self._items[key]

    def delete_term(self, term: str) -> bool:
        """
        Xóa một thuật ngữ khỏi kho.

        Returns:
            True nếu xóa thành công, False nếu không tìm thấy.
        """
        key = term.upper()
        if key not in self._items:
            return False
        del self._items[key]
        self.save()
        logger.info(f"Deleted glossary term: '{term}'")
        return True

    def search(
        self,
        query: str = "",
        domain: str | None = None,
    ) -> list[GlossaryItem]:
        """
        Tìm kiếm từ điển theo keyword hoặc lĩnh vực.

        Args:
            query: Từ khóa tìm kiếm (tìm trong term, full_name_vi, full_name_en).
            domain: Lọc theo lĩnh vực.

        Returns:
            Danh sách GlossaryItem phù hợp.
        """
        results = list(self._items.values())

        if domain:
            results = [item for item in results if item.domain.lower() == domain.lower()]

        if query:
            q = query.lower()
            results = [
                item for item in results
                if q in item.term.lower()
                or q in item.full_name_vi.lower()
                or q in item.full_name_en.lower()
                or q in item.description.lower()
            ]

        return results
