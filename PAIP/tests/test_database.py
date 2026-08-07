"""
Unit tests for PAIP Database Session & ORM Models
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from core.database.session import init_db, async_session_factory
from core.database.models import (
    SystemRule,
    UserFeedback,
    UserCorrection,
    ExperienceMemory,
    ProofreadHistory,
)


@pytest.mark.asyncio
async def test_init_db_and_seeded_rules():
    """Verify that init_db creates all tables and seeds default system rules."""
    await init_db()
    async with async_session_factory() as session:
        stmt = select(SystemRule)
        rules = (await session.execute(stmt)).scalars().all()
        assert len(rules) >= 5
        codes = [r.rule_code for r in rules]
        assert "GLOSSARY-PTSC" in codes
        assert "FORMAT-ND30" in codes
        assert "CA-001" in codes
        assert "CA-002" in codes
        assert "CA-003" in codes


@pytest.mark.asyncio
async def test_user_feedback_crud():
    """Verify UserFeedback creation and querying."""
    async with async_session_factory() as session:
        feedback = UserFeedback(
            error_original="PTSC QNg",
            error_suggested="PTSC Quảng Ngãi",
            error_type="glossary",
            action="accept",
            user_id="user_test_01",
        )
        session.add(feedback)
        await session.commit()
        assert feedback.id is not None

        # Query back
        stmt = select(UserFeedback).where(UserFeedback.id == feedback.id)
        fetched = (await session.execute(stmt)).scalar_one_or_none()
        assert fetched is not None
        assert fetched.action == "accept"
        assert fetched.error_type == "glossary"


@pytest.mark.asyncio
async def test_user_correction_crud():
    """Verify UserCorrection creation (missed error report)."""
    async with async_session_factory() as session:
        correction = UserCorrection(
            document_snippet="Hạn nộp hồ sơ trước ngày ban hành",
            error_text="20/12/2025",
            suggested_fix="20/12/2026",
            error_category="consistency",
            status="pending",
            user_id="user_test_02",
        )
        session.add(correction)
        await session.commit()
        assert correction.id is not None
        assert correction.status == "pending"
        assert correction.verified_count == 1


@pytest.mark.asyncio
async def test_experience_memory_crud():
    """Verify ExperienceMemory creation for dynamic Few-shot."""
    async with async_session_factory() as session:
        memory = ExperienceMemory(
            category="glossary",
            original_text="Dự án tại PTSC QNg",
            corrected_text="Dự án tại PTSC Quảng Ngãi",
            explanation="Chuẩn nhận diện thương hiệu",
            trust_score=1.5,
        )
        session.add(memory)
        await session.commit()
        assert memory.id is not None
        assert memory.trust_score == 1.5


@pytest.mark.asyncio
async def test_proofread_history_crud():
    """Verify ProofreadHistory audit logging."""
    async with async_session_factory() as session:
        history = ProofreadHistory(
            filename="Thu_moi_chao_gia.docx",
            input_type="file",
            overall_score=8.7,
            spelling_score=9.5,
            format_score=7.0,
            glossary_score=10.0,
            consistency_score=8.5,
            total_errors=2,
            tokens_used=520,
            processing_time_ms=340.2,
        )
        session.add(history)
        await session.commit()
        assert history.id is not None
        assert history.overall_score == 8.7
