"""
Unit & Integration Tests — PAIP Core Database Layer.

Kiểm thử:
1. Khởi tạo Database Schema (init_db)
2. Seed Data tự động (seed_default_data)
3. Các Models: Glossary, Auth/RBAC, Telemetry, Agent History
4. DatabaseGlossaryLoader: Nạp từ CSDL vào RAM và tích hợp RuleEngine
"""

import pytest
from sqlalchemy import func, select

from core.database import (
    AsyncSessionLocal,
    init_db,
    seed_default_data,
)
from core.database.models import (
    Agent0ProofreadHistoryModel,
    AuditLogModel,
    DepartmentModel,
    GlossaryTermModel,
    LLMRequestModel,
    RoleModel,
    UserModel,
)
from core.rule_engine.context import RuleContext
from core.rule_engine.engine import RuleEngine
from core.rule_engine.loaders.db_loader import DatabaseGlossaryLoader


@pytest.mark.asyncio
class TestDatabaseCore:
    """Test suite cho toàn bộ hạ tầng Database."""

    async def test_init_and_seed_database(self):
        """Khởi tạo database và nạp dữ liệu mặc định thành công."""
        await init_db()
        await seed_default_data()

        async with AsyncSessionLocal() as session:
            # 1. Kiểm tra Glossary Terms
            glossary_count = await session.scalar(select(func.count(GlossaryTermModel.id)))
            assert glossary_count >= 20, f"Expected at least 20 terms, got {glossary_count}"

            # 2. Kiểm tra Roles
            role_count = await session.scalar(select(func.count(RoleModel.id)))
            assert role_count >= 4, f"Expected at least 4 roles, got {role_count}"

            # 3. Kiểm tra Departments
            dept_count = await session.scalar(select(func.count(DepartmentModel.id)))
            assert dept_count >= 6, f"Expected at least 6 departments, got {dept_count}"

    async def test_glossary_crud_operations(self):
        """Kiểm tra các thao tác Thêm / Sửa / Xóa trên GlossaryTermModel."""
        await init_db()

        test_term_name = "TEST_TERM_DB"
        async with AsyncSessionLocal() as session:
            # Clean up if exists
            existing = await session.scalar(
                select(GlossaryTermModel).where(GlossaryTermModel.term == test_term_name)
            )
            if existing:
                await session.delete(existing)
                await session.commit()

            # 1. Create
            new_term = GlossaryTermModel(
                term=test_term_name,
                standard_case="Test_Term_DB",
                full_name_vi="Thuật ngữ kiểm thử Database",
                full_name_en="Test Database Term",
                domain="TestDomain",
                incorrect_variants=["test_term", "test term db"],
                synonyms=["TTDB"],
                do_not_translate=True,
                description="Dùng trong unit test",
            )
            session.add(new_term)
            await session.commit()
            await session.refresh(new_term)
            assert new_term.id is not None
            term_id = new_term.id

        # 2. Read & Update
        async with AsyncSessionLocal() as session:
            fetched = await session.get(GlossaryTermModel, term_id)
            assert fetched is not None
            assert fetched.term == test_term_name
            fetched.description = "Updated description"
            await session.commit()

        # 3. Verify Update & Delete
        async with AsyncSessionLocal() as session:
            updated = await session.get(GlossaryTermModel, term_id)
            assert updated.description == "Updated description"
            await session.delete(updated)
            await session.commit()

        async with AsyncSessionLocal() as session:
            deleted = await session.get(GlossaryTermModel, term_id)
            assert deleted is None

    async def test_auth_and_telemetry_models(self):
        """Kiểm tra quan hệ giữa User, Department, AuditLog, LLMRequest, Agent0History."""
        await init_db()

        async with AsyncSessionLocal() as session:
            # Tạo phòng ban test
            dept = DepartmentModel(code="TEST_DEPT", name="Phòng Thử Nghiệm")
            session.add(dept)
            await session.flush()

            # Tạo user test
            user = UserModel(
                username="test_dev_user",
                email="dev_test@ptsc.com.vn",
                full_name="Nguyễn Văn Test",
                department_id=dept.id,
            )
            session.add(user)
            await session.flush()

            # Tạo audit log
            audit = AuditLogModel(
                user_id=user.id,
                action="TEST_ACTION",
                resource_type="test",
                resource_id="123",
            )
            session.add(audit)

            # Tạo LLM request record
            llm_req = LLMRequestModel(
                user_id=user.id,
                department_id=dept.id,
                agent_id="agent_0_proofreader",
                provider="gemini",
                model_name="gemini-2.5-flash",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                latency_ms=450.0,
                estimated_cost_usd=0.0001,
            )
            session.add(llm_req)

            # Tạo Agent 0 history
            history = Agent0ProofreadHistoryModel(
                user_id=user.id,
                filename="test_doc.docx",
                mode="formal",
                char_count=500,
                total_errors=2,
                score=9.5,
                violations_summary={"GLOSSARY": 2},
                processing_time_ms=620.0,
            )
            session.add(history)

            await session.commit()

            # Assert IDs generated
            assert dept.id is not None
            assert user.id is not None
            assert audit.id is not None
            assert llm_req.id is not None
            assert history.id is not None

            # Clean up
            await session.delete(history)
            await session.delete(llm_req)
            await session.delete(audit)
            await session.delete(user)
            await session.delete(dept)
            await session.commit()

    async def test_database_glossary_loader_and_rule_engine(self):
        """Kiểm tra DatabaseGlossaryLoader nạp dữ liệu từ DB vào RAM và RuleEngine quét chính xác."""
        await init_db()
        await seed_default_data()

        loader = DatabaseGlossaryLoader()
        count = await loader.load_async()
        assert count >= 20
        assert loader.is_loaded is True

        # Test search in memory
        item = loader.get("FPSO")
        assert item is not None
        assert item.term == "FPSO"

        # Test RuleEngine with Database loader
        engine = RuleEngine(loader=loader)
        engine.load()

        context = RuleContext(text="Cần thuê tàu fpso cho dự án mỏ Sư Tử Trắng của PTSC QNG.")
        result = engine.evaluate(context)

        # Vi phạm fpso -> FPSO
        assert result.has_violations is True
        error_terms = [v.original_text.lower() for v in result.violations]
        assert "fpso" in error_terms

        # Whitelist contains PTSC QNG
        assert any("PTSC" in w for w in result.whitelist_terms)
