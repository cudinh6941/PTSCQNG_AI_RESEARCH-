# 🏛️ PAIP — Enterprise Database Specification

> **Module:** Core Infrastructure / Database & Persistence  
> **Target Engine:** PostgreSQL 16+ (Dev/Local: SQLite Async)  
> **ORM Layer:** SQLAlchemy 2.0 (Async) + Alembic  
> **Obsidian Source:** `PTSC_AI_RnD/Architecture/Database_Architecture.md`

Xem tài liệu kiến trúc đầy đủ chi tiết tại kho tri thức Obsidian:
👉 [Database_Architecture.md](file:///d:/AI_R&D/PTSC_AI_RnD/Architecture/Database_Architecture.md)

---

## Tóm Tắt 4 Phân Hệ Bảng (Schemas)

1. **System & Rules:**
   - `glossary_terms`: Thuật ngữ chuẩn, biến thể sai (JSONB), domain, cấm dịch.
   - `system_rules`: Bộ luật thể thức và quy trình (Level 2 & 3).
   - `system_settings`: Cấu hình hệ thống động.

2. **Auth & RBAC:**
   - `departments`: Cây tổ chức phòng ban PTSC (P.ATCL, P.KTTB...).
   - `users`: Tài khoản đồng bộ từ LDAP (`sAMAccountName`, email, phòng ban).
   - `roles` & `permissions` & `user_roles`: Ma trận phân quyền doanh nghiệp.
   - `user_sessions`: Quản lý phiên đăng nhập và token refresh.

3. **Audit & Telemetry:**
   - `audit_logs`: Nhật ký kiểm toán thao tác hệ thống.
   - `llm_requests`: Thống kê token và chi phí USD theo từng user/phòng ban.
   - `department_quotas`: Quản lý hạn mức ngân sách AI hàng tháng.

4. **Agents Data (Dài hạn):**
   - `agent0_proofread_history`: Lịch sử rà soát văn bản của Agent 0.
   - `agent1_meeting_sessions`: Dữ liệu cuộc họp của Agent 1.
   - `agent2_documents` & `agent2_document_chunks`: Dữ liệu RAG với PostgreSQL `pgvector`.
