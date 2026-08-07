"""
PAIP Database Session Management & Async Initialization
Supports SQLite Async (aiosqlite) in Dev & PostgreSQL in Production
"""

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base, SystemRule

# Database URL from env or default SQLite Async
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./paip.db")

# Create Async Engine
# For SQLite, check_same_thread=False is needed
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)

# Async Session Factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for background jobs or scripts."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and seed default system rules."""
    try:
        logger.info(f"Initializing database at: {DATABASE_URL}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Seed default rules if empty
        async with async_session_factory() as session:
            stmt = select(SystemRule).limit(1)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                logger.info("Seeding default system rules into database...")
                default_rules = [
                    SystemRule(
                        rule_code="GLOSSARY-PTSC",
                        rule_type="glossary",
                        name="Quy chuẩn Nhận diện Thương hiệu PTSC",
                        description="Kiểm tra viết đúng tên công ty PTSC Quảng Ngãi và các thuật ngữ chuyên ngành Dầu khí/Cơ khí.",
                        severity="HIGH",
                        is_active=True,
                    ),
                    SystemRule(
                        rule_code="FORMAT-ND30",
                        rule_type="format",
                        name="Thể thức Văn bản Nghị định 30/2020/NĐ-CP",
                        description="Kiểm tra căn lề A4 (3-1.5-2-2cm), font Times New Roman và căn đều Justified.",
                        severity="MEDIUM",
                        is_active=True,
                    ),
                    SystemRule(
                        rule_code="CA-001",
                        rule_type="consistency",
                        name="Đối soát Số hiệu Văn bản",
                        description="Kiểm tra tính nhất quán của số hiệu văn bản giữa Header và Phụ lục đính kèm.",
                        severity="HIGH",
                        is_active=True,
                    ),
                    SystemRule(
                        rule_code="CA-002",
                        rule_type="consistency",
                        name="Đối soát Số tiền bằng số và bằng chữ",
                        description="Kiểm tra giá trị số tiền bằng số và số tiền viết bằng chữ có trùng khớp 100% hay không.",
                        severity="HIGH",
                        is_active=True,
                    ),
                    SystemRule(
                        rule_code="CA-003",
                        rule_type="consistency",
                        name="Kiểm tra Logic Thời gian & Hiệu lực",
                        description="Phát hiện nghịch lý ngày ban hành sau hạn nộp hồ sơ hoặc thời hạn không hợp lý.",
                        severity="HIGH",
                        is_active=True,
                    ),
                ]
                session.add_all(default_rules)
                await session.commit()
                logger.info(f"Seeded {len(default_rules)} default system rules.")
        
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
