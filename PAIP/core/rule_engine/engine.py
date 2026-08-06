"""
Rule Engine — Main Engine (Pipeline Orchestrator).

Class trung tâm điều phối toàn bộ pipeline:
1. Khởi tạo & nạp dữ liệu từ điển.
2. Compile Regex patterns vào RAM.
3. Chạy các Rules theo thứ tự ưu tiên.
4. Hợp nhất kết quả.

Sử dụng Singleton pattern để dùng chung một instance toàn ứng dụng.
"""

from __future__ import annotations

import time
from pathlib import Path

from core.common.logger import logger

from .base import RuleResult, RuleViolation
from .context import RuleContext
from .loaders.db_loader import DatabaseGlossaryLoader
from .loaders.json_loader import GlossaryItem, GlossaryLoader
from .rules.glossary_rule import GlossaryRule


# Đường dẫn mặc định đến thư mục data (cho JSON fallback)
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


class RuleEngine:
    """
    Bộ máy thực thi quy tắc (Rule Engine) cho PAIP.

    Chức năng chính:
    - Quản lý vòng đời: init → load từ Database → compile Regex vào RAM → evaluate.
    - Hợp nhất kết quả từ nhiều Rules.
    - Hot-reload: Nạp lại dữ liệu từ CSDL mà không cần restart server.
    """

    def __init__(
        self,
        loader: DatabaseGlossaryLoader | GlossaryLoader | None = None,
        data_dir: str | Path | None = None,
    ):
        self._data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self._is_loaded = False

        # Khởi tạo Loader: Mặc định là DatabaseGlossaryLoader
        if loader is not None:
            self._glossary_loader = loader
        else:
            self._glossary_loader = DatabaseGlossaryLoader()

        self._glossary_rule = GlossaryRule(loader=self._glossary_loader)

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def glossary_count(self) -> int:
        return len(self._glossary_loader.get_all_terms())

    @property
    def glossary_loader(self) -> DatabaseGlossaryLoader | GlossaryLoader:
        return self._glossary_loader

    # ── Lifecycle ─────────────────────────────────────────

    def load(self) -> None:
        """
        Nạp toàn bộ dữ liệu từ file & compile Regex patterns.

        Gọi phương thức này khi ứng dụng khởi động (startup event).
        """
        logger.info("RuleEngine: Loading data...")
        self._glossary_loader.load()
        self._glossary_rule.compile()
        self._is_loaded = True
        logger.info(
            f"RuleEngine: Ready — {self._glossary_loader.count} glossary terms loaded."
        )

    def reload(self) -> dict:
        """
        Hot-reload: Nạp lại toàn bộ dữ liệu từ file & recompile.

        Returns:
            Dict summary: {"glossary_count": N, "reload_time_ms": X}
        """
        start = time.perf_counter()
        logger.info("RuleEngine: Hot-reloading...")
        self._glossary_loader.load()
        self._glossary_rule.compile()
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"RuleEngine: Reloaded in {elapsed_ms:.1f}ms — "
            f"{self._glossary_loader.count} glossary terms."
        )
        return {
            "glossary_count": self._glossary_loader.count,
            "reload_time_ms": round(elapsed_ms, 2),
        }

    # ── Core Evaluation ──────────────────────────────────

    def evaluate(self, context: RuleContext) -> RuleResult:
        """
        Chạy toàn bộ pipeline Rules trên một RuleContext.

        Luồng xử lý:
        1. Chạy GlossaryRule (Level 1 — Siêu tốc).
        2. (Future) Chạy FormatRule (Level 2).
        3. (Future) Chạy ProcessRule (Level 3).
        4. Hợp nhất kết quả.

        Args:
            context: RuleContext chứa text + metadata.

        Returns:
            RuleResult tổng hợp từ tất cả Rules.
        """
        if not self._is_loaded:
            self.load()

        start_time = time.perf_counter()

        # ── Level 1: Glossary ─────────────────────────────
        glossary_result = self._glossary_rule.evaluate(context)

        # ── Level 2: Format (Future) ──────────────────────
        # format_result = self._format_rule.evaluate(context)

        # ── Level 3: Process (Future) ─────────────────────
        # process_result = self._process_rule.evaluate(context)

        # ── Merge Results ─────────────────────────────────
        merged = RuleResult(
            violations=glossary_result.violations,
            detected_terms=glossary_result.detected_terms,
            whitelist_terms=glossary_result.whitelist_terms,
            prompt_injection=glossary_result.prompt_injection,
            processing_time_ms=(time.perf_counter() - start_time) * 1000,
        )

        return merged

    # ── CRUD Proxy (Delegate to Loader) ───────────────────

    def get_all_glossary_terms(self) -> list[GlossaryItem]:
        """Lấy toàn bộ từ điển."""
        return list(self._glossary_loader.get_all_terms().values())

    def get_glossary_term(self, term: str) -> GlossaryItem | None:
        """Tìm một thuật ngữ theo tên."""
        return self._glossary_loader.get_term(term)

    def add_glossary_term(self, item: GlossaryItem) -> GlossaryItem:
        """Thêm thuật ngữ mới & auto-recompile."""
        result = self._glossary_loader.add_term(item)
        self._glossary_rule.compile()  # Re-compile để cập nhật patterns
        return result

    def update_glossary_term(self, term: str, updates: dict) -> GlossaryItem:
        """Cập nhật thuật ngữ & auto-recompile."""
        result = self._glossary_loader.update_term(term, updates)
        self._glossary_rule.compile()
        return result

    def delete_glossary_term(self, term: str) -> bool:
        """Xóa thuật ngữ & auto-recompile."""
        success = self._glossary_loader.delete_term(term)
        if success:
            self._glossary_rule.compile()
        return success

    def search_glossary(
        self, query: str = "", domain: str | None = None
    ) -> list[GlossaryItem]:
        """Tìm kiếm từ điển."""
        return self._glossary_loader.search(query=query, domain=domain)


# ── Singleton Instance ────────────────────────────────────
# Import và sử dụng: from core.rule_engine import rule_engine

rule_engine = RuleEngine()
