"""
Rule Engine — Database Loader.

Đọc dữ liệu từ điển trực tiếp từ bảng glossary_terms trong CSDL (SQLite / PostgreSQL)
và nạp vào bộ nhớ RAM cho GlossaryRule biên dịch Regex siêu tốc (< 1ms).
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional
from loguru import logger
from sqlalchemy import select

from core.database.engine import AsyncSessionLocal, init_db
from core.database.models.glossary import GlossaryTermModel
from core.database.seed import seed_default_data
from core.rule_engine.loaders.json_loader import GlossaryItem


class DatabaseGlossaryLoader:
    """
    Quản lý nạp từ điển từ CSDL vào RAM cho Rule Engine.
    Hỗ trợ cả async load và đồng bộ (qua asyncio runner nếu cần).
    """

    def __init__(self) -> None:
        self._items: Dict[str, GlossaryItem] = {}  # Key: UPPERCASE term
        self._is_loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def count(self) -> int:
        return len(self._items)

    async def load_async(self) -> int:
        """
        Query tất cả GlossaryTermModel từ CSDL và lưu vào RAM dictionary.
        Nếu bảng rỗng hoặc chưa tạo, tự động init và seed dữ liệu mặc định.
        """
        try:
            async with AsyncSessionLocal() as session:
                stmt = select(GlossaryTermModel).where(GlossaryTermModel.is_active == True)
                result = await session.scalars(stmt)
                db_terms = result.all()
        except Exception:
            logger.info("Database schema not yet initialized. Initializing and seeding...")
            await init_db()
            await seed_default_data()
            async with AsyncSessionLocal() as session:
                stmt = select(GlossaryTermModel).where(GlossaryTermModel.is_active == True)
                result = await session.scalars(stmt)
                db_terms = result.all()

        if len(db_terms) == 0:
            logger.info("Database glossary terms table is empty. Running seed_default_data()...")
            await seed_default_data()
            async with AsyncSessionLocal() as session:
                stmt = select(GlossaryTermModel).where(GlossaryTermModel.is_active == True)
                result = await session.scalars(stmt)
                db_terms = result.all()

        items: Dict[str, GlossaryItem] = {}
        for row in db_terms:
            item = GlossaryItem(
                term=row.term,
                standard_case=row.standard_case or row.term,
                full_name_vi=row.full_name_vi or "",
                full_name_en=row.full_name_en or "",
                domain=row.domain or "General",
                incorrect_variants=list(row.incorrect_variants or []),
                synonyms=list(row.synonyms or []),
                do_not_translate=bool(row.do_not_translate),
                description=row.description or "",
            )
            items[row.term.upper()] = item

        self._items = items
        self._is_loaded = True
        logger.info(f"DatabaseGlossaryLoader: Loaded {len(self._items)} active glossary terms from Database.")
        return len(self._items)

    def load(self) -> int:
        """
        Phương thức nạp đồng bộ (dùng khi engine khởi động hoặc trong context synchronous).
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(lambda: asyncio.run(self.load_async())).result()
            else:
                return loop.run_until_complete(self.load_async())
        except Exception as e:
            logger.warning(f"DatabaseGlossaryLoader: Async load fallback triggering asyncio.run: {e}")
            return asyncio.run(self.load_async())

    def get_all_terms(self) -> Dict[str, GlossaryItem]:
        """Trả về toàn bộ dictionary thuật ngữ (Key: UPPERCASE)."""
        return self._items

    def get_term(self, term: str) -> Optional[GlossaryItem]:
        """Tra cứu một thuật ngữ theo tên (không phân biệt hoa/thường)."""
        return self._items.get(term.strip().upper())

    def get(self, term: str) -> Optional[GlossaryItem]:
        """Alias cho get_term."""
        return self.get_term(term)

    def get_all(self) -> List[GlossaryItem]:
        """Trả về danh sách tất cả GlossaryItem."""
        return list(self._items.values())

    def get_domains(self) -> List[str]:
        """Trả về danh sách các lĩnh vực (domain) duy nhất."""
        return sorted(list(set(item.domain for item in self._items.values())))

    def search(
        self,
        query: str = "",
        domain: str = "",
    ) -> List[GlossaryItem]:
        """
        Tìm kiếm thuật ngữ theo từ khóa và/hoặc domain trong RAM.
        """
        results = list(self._items.values())

        if domain:
            domain_lower = domain.strip().lower()
            results = [item for item in results if item.domain.lower() == domain_lower]

        if query:
            q = query.strip().lower()
            results = [
                item for item in results
                if q in item.term.lower()
                or q in item.full_name_vi.lower()
                or q in item.full_name_en.lower()
                or any(q in v.lower() for v in item.incorrect_variants)
                or any(q in s.lower() for s in item.synonyms)
            ]

        return results

    def add_term(self, item: GlossaryItem) -> GlossaryItem:
        """Thêm thuật ngữ vào RAM cache."""
        key = item.term.strip().upper()
        self._items[key] = item
        return item

    def update_term(self, term: str, updates: dict) -> GlossaryItem:
        """Cập nhật thuật ngữ trong RAM cache."""
        key = term.strip().upper()
        if key not in self._items:
            raise KeyError(f"Thuật ngữ '{term}' không tồn tại trong từ điển.")

        current = self._items[key]
        current_data = current.model_dump()
        current_data.update({k: v for k, v in updates.items() if v is not None})
        updated_item = GlossaryItem(**current_data)
        self._items[key] = updated_item
        return updated_item

    def delete_term(self, term: str) -> bool:
        """Xóa thuật ngữ khỏi RAM cache."""
        key = term.strip().upper()
        if key in self._items:
            del self._items[key]
            return True
        return False
