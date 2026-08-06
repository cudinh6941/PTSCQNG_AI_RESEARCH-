"""
PAIP Core Database — Async Engine & Session Factory.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.common.config import Settings
from core.database.base import Base


_settings = Settings()

# Ensure local data directory exists if using SQLite
if "sqlite" in _settings.database_url:
    db_path_str = _settings.database_url.split("///")[-1]
    db_file_path = Path(db_path_str)
    if not db_file_path.is_absolute():
        db_file_path = Path.cwd() / db_file_path
    db_file_path.parent.mkdir(parents=True, exist_ok=True)

# Create Async Engine
_engine_kwargs = {
    "echo": _settings.db_echo_sql,
    "future": True,
}

# PostgreSQL specific pool optimizations
if "postgresql" in _settings.database_url:
    _engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    **_engine_kwargs,
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency that yields an AsyncSession per request.
    Automatically closes session upon completion.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database schema (create all tables if not exist).
    In production with migrations, Alembic will manage schema versions.
    """
    logger.info("Initializing database schema...")
    # Import all models to ensure metadata is registered with Base
    import core.database.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
