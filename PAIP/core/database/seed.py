"""
PAIP Core Database — Automatic Seed Data Initialization.
"""

from __future__ import annotations

import json
from pathlib import Path
from loguru import logger
from sqlalchemy import select, func

from core.database.engine import AsyncSessionLocal
from core.database.models import (
    DepartmentModel,
    GlossaryTermModel,
    RoleModel,
)


_GLOSSARY_JSON_PATH = Path(__file__).resolve().parent.parent / "rule_engine" / "data" / "glossary.json"


async def seed_default_data() -> None:
    """
    Seed initial platform data if database tables are empty:
    1. 24 default PTSC Glossary terms from glossary.json
    2. Default RBAC Roles (ADMIN, DEPT_LEAD, SPECIALIST, VIEWER)
    3. Default PTSC Departments (P.ATCL, P.KTTB, P.TM, P.TCKT, P.TCHC, XN.CL)
    """
    async with AsyncSessionLocal() as session:
        # 1. Seed Glossary Terms
        glossary_count = await session.scalar(select(func.count(GlossaryTermModel.id)))
        if glossary_count == 0 and _GLOSSARY_JSON_PATH.exists():
            try:
                with open(_GLOSSARY_JSON_PATH, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                if isinstance(raw_data, dict):
                    if "terms" in raw_data and isinstance(raw_data["terms"], list):
                        terms_list = raw_data["terms"]
                    else:
                        terms_list = list(raw_data.values())
                elif isinstance(raw_data, list):
                    terms_list = raw_data
                else:
                    terms_list = []

                for t in terms_list:
                    if not isinstance(t, dict) or "term" not in t:
                        continue
                    model = GlossaryTermModel(
                        term=t["term"].strip(),
                        standard_case=t.get("standard_case", t["term"]).strip(),
                        full_name_vi=t.get("full_name_vi"),
                        full_name_en=t.get("full_name_en"),
                        domain=t.get("domain", "General"),
                        incorrect_variants=t.get("incorrect_variants", []),
                        synonyms=t.get("synonyms", []),
                        do_not_translate=t.get("do_not_translate", True),
                        description=t.get("description"),
                        is_active=t.get("is_active", True),
                    )
                    session.add(model)
                logger.info(f"Seeded {len(terms_list)} glossary terms into database.")
            except Exception as e:
                logger.error(f"Error seeding glossary data: {e}")

        # 2. Seed Default Roles
        role_count = await session.scalar(select(func.count(RoleModel.id)))
        if role_count == 0:
            default_roles = [
                RoleModel(name="ADMIN", description="Quản trị viên tối cao hệ thống", is_system=True),
                RoleModel(name="DEPT_LEAD", description="Trưởng/Phó phòng ban, phê duyệt quy chuẩn", is_system=True),
                RoleModel(name="SPECIALIST", description="Chuyên viên nghiệp vụ, sử dụng các AI Agent", is_system=True),
                RoleModel(name="VIEWER", description="Chỉ xem kết quả, không chỉnh sửa", is_system=True),
            ]
            session.add_all(default_roles)
            logger.info("Seeded 4 default RBAC roles into database.")

        # 3. Seed Default Departments
        dept_count = await session.scalar(select(func.count(DepartmentModel.id)))
        if dept_count == 0:
            default_depts = [
                DepartmentModel(code="P.ATCL", name="Phòng An toàn Chất lượng (HSEQ)"),
                DepartmentModel(code="P.KTTB", name="Phòng Kỹ thuật Thiết bị"),
                DepartmentModel(code="P.TM", name="Phòng Thương mại & Đấu thầu"),
                DepartmentModel(code="P.TCKT", name="Phòng Tài chính Kế toán"),
                DepartmentModel(code="P.TCHC", name="Phòng Tổ chức Hành chính"),
                DepartmentModel(code="XN.CL", name="Xí nghiệp Cơ khí & Xây lắp"),
            ]
            session.add_all(default_depts)
            logger.info("Seeded 6 default PTSC departments into database.")

        await session.commit()
