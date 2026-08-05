# 🔐 Kế hoạch & Kiến trúc Tích hợp LDAP / Active Directory (Auth & DB Spec)

> **Dự án:** PAIP — PTSC AI Platform  
> **Trạng thái:** Sẵn sàng triển khai (Ready for Implementation)  
> **Tài liệu tham chiếu:** `PTSC_AI_RnD/Architecture/PAIP_Architecture.md`

---

## 1. Tổng quan & Mục tiêu

Tích hợp xác thực tập trung thông qua máy chủ **LDAP / Active Directory (AD)** của PTSC kết hợp **JWT (JSON Web Token)** và **Cơ sở dữ liệu nội bộ (Local DB)** để đạt được:
- ✅ **Đăng nhập một lần (Single Sign-On)** bằng tài khoản nội bộ công ty (sAMAccountName hoặc email).
- ✅ **Cơ chế JIT Provisioning (Just-In-Time)**: Tự động đồng bộ và tạo tài khoản vào DB nội bộ ở lần đăng nhập đầu tiên.
- ✅ **Quản lý Hạn mức & Chi phí AI (Cost & Quota Tracking)**: Theo dõi token OpenAI / Gemini / Claude tiêu thụ theo từng user/phòng ban.
- ✅ **Phân quyền chi tiết (RBAC)**: Map các nhóm từ Active Directory (`memberOf`) sang vai trò nội bộ của PAIP.
- ✅ **Lịch sử & Audit Log**: Ghi nhận hoạt động truy cập và sử dụng AI Agent để đảm bảo an toàn thông tin doanh nghiệp.

---

## 2. Sơ đồ Kiến trúc & Luồng xác thực

```mermaid
sequenceDiagram
    autonumber
    actor User as Nhân viên (Web UI / API Client)
    participant PAIP as FastAPI Backend (PAIP)
    participant LDAP as PTSC Active Directory / LDAP Server
    participant DB as Internal Database (SQLite / Postgres)

    User->>PAIP: 1. Gửi request POST /api/v1/auth/login (username, password)
    PAIP->>LDAP: 2. Direct Bind / Search (Kiểm tra mật khẩu & lấy user attributes)
    
    alt Mật khẩu sai / Tài khoản khóa
        LDAP-->>PAIP: Bind Failed
        PAIP-->>User: 401 Unauthorized (Sai thông tin đăng nhập)
    else Xác thực thành công
        LDAP-->>PAIP: Trả về profile (displayName, mail, department, memberOf)
        PAIP->>DB: 3. Upsert User (Đồng bộ thông tin, map role từ AD Group)
        PAIP->>DB: 4. Kiểm tra trạng thái tài khoản & Quota khả dụng
        PAIP->>PAIP: 5. Tạo cặp JWT Token (Access Token 30p + Refresh Token 7 ngày)
        PAIP-->>User: 6. Trả về Token + User Profile & Quyền hạn
    end

    Note over User,PAIP: Các request gọi AI Agent tiếp theo
    User->>PAIP: Gửi request + Header "Authorization: Bearer <access_token>"
    PAIP->>PAIP: Verify JWT cục bộ (Không cần query lại LDAP)
    PAIP->>DB: Ghi nhận Token Usage & Audit Log
    PAIP-->>User: Trả về kết quả xử lý từ AI Agent
```

---

## 3. Thiết kế Cơ sở dữ liệu (Database Schema)

Database sử dụng **SQLAlchemy / SQLModel** (hỗ trợ SQLite cho dev và PostgreSQL cho production).

### 3.1. Bảng `users`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK) | Khóa chính tự tăng |
| `username` | String (Unique, Index) | Khớp với `sAMAccountName` trên Active Directory |
| `email` | String (Index) | Email nội bộ (VD: `anhnv@ptsc.com.vn`) |
| `full_name` | String | Họ tên nhân viên (VD: Nguyễn Văn Anh) |
| `department` | String | Phòng ban (VD: Phòng Pháp chế, Ban Đấu thầu) |
| `title` | String | Chức danh / Vị trí |
| `role` | String (Enum) | `admin`, `lead_reviewer`, `standard_user` |
| `is_active` | Boolean | Trạng thái kích hoạt (Default: `True`) |
| `is_local_admin` | Boolean | Tài khoản quản trị nội bộ fallback (Default: `False`) |
| `hashed_password` | String (Nullable) | Chỉ dùng cho local fallback admin |
| `monthly_quota_usd` | Float | Hạn mức chi phí AI tối đa / tháng (Default: `10.0`) |
| `created_at` | DateTime | Thời gian tạo tài khoản |
| `last_login_at` | DateTime | Thời gian đăng nhập gần nhất |

### 3.2. Bảng `token_usages`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK) | Khóa chính |
| `user_id` | Integer (FK `users.id`) | Người thực hiện |
| `agent_name` | String | Tên agent (e.g. `agent_0_proofreader`) |
| `provider` | String | `gemini`, `openai`, `anthropic` |
| `model` | String | Tên model (e.g. `gemini-2.5-flash`) |
| `input_tokens` | Integer | Số lượng prompt tokens |
| `output_tokens` | Integer | Số lượng completion tokens |
| `cost_usd` | Float | Chi phí ước tính theo USD |
| `created_at` | DateTime | Thời điểm gọi LLM |

### 3.3. Bảng `audit_logs`
| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | Integer (PK) | Khóa chính |
| `user_id` | Integer (FK `users.id`) | Người thao tác |
| `action` | String | Hành động (`LOGIN`, `UPLOAD_FILE`, `RUN_PROOFREAD`) |
| `resource` | String | Tên file / endpoint xử lý |
| `ip_address` | String | Địa chỉ IP người dùng |
| `status` | String | `SUCCESS` hoặc `FAILED` |
| `details` | Text / JSON | Chi tiết lỗi hoặc thông tin bổ sung |
| `created_at` | DateTime | Thời gian ghi log |

---

## 4. Cấu hình biến môi trường (`.env`)

Cần bổ sung các biến sau vào file `.env`:

```env
# ============================================================
# LDAP / Active Directory Configuration
# ============================================================
LDAP_SERVER_URI=ldaps://dc.ptsc.com.vn:636
LDAP_BASE_DN=DC=ptsc,DC=com,DC=vn
LDAP_BIND_USER_DN=CN=svc_paip,OU=ServiceAccounts,DC=ptsc,DC=com,DC=vn
LDAP_BIND_USER_PASSWORD=your-service-account-password
LDAP_USER_SEARCH_FILTER=(|(sAMAccountName={username})(mail={username}))
LDAP_USE_TLS=true
LDAP_CONNECT_TIMEOUT=5

# Role Mapping từ AD Group sang PAIP Role (cách nhau bởi dấu phẩy)
LDAP_ADMIN_GROUPS=CN=AI_Admins,OU=Groups,DC=ptsc,DC=com,DC=vn
LDAP_REVIEWER_GROUPS=CN=Legal_Reviewers,OU=Groups,DC=ptsc,DC=com,DC=vn

# ============================================================
# JWT Security
# ============================================================
JWT_SECRET_KEY=generate-a-super-secret-64-character-hex-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================================
# Database Configuration
# ============================================================
DATABASE_URL=sqlite:///./paip.db
# Production Postgres: postgresql+asyncpg://paip_user:password@localhost:5432/paip
```

---

## 5. Cấu trúc Source Code cần triển khai

```
PAIP/
├── core/
│   ├── auth/                          ← [NEW] Module xác thực & bảo mật
│   │   ├── __init__.py
│   │   ├── ldap_client.py             ← Xử lý kết nối LDAP3, authenticate & query profile
│   │   ├── jwt_handler.py             ← Tạo & xác thực Access / Refresh JWT Token
│   │   └── dependencies.py            ← FastAPI Dependencies: get_current_user, require_role
│   │
│   ├── db/                            ← [NEW] Quản lý Database & ORM
│   │   ├── __init__.py
│   │   ├── session.py                 ← Async engine & session factory
│   │   └── models.py                  ← ORM Models (User, TokenUsage, AuditLog)
│   │
│   └── common/
│       └── config.py                  ← Bổ sung cấu hình LDAP, JWT, DB
│
├── api/
│   ├── routers/
│   │   └── auth.py                    ← [NEW] Endpoints: /login, /refresh, /me, /logout
│   └── main.py                        ← Tích hợp Auth Router & Exception handlers
```

---

## 6. Kế hoạch triển khai từng bước (Step-by-Step Execution Plan)

### Bước 1: Cài đặt thư viện phụ thuộc
Thêm vào `requirements.txt`:
```txt
# --- Authentication & LDAP ---
ldap3>=2.9.1
pyjwt[crypto]>=2.9.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.2.0

# --- Database & ORM ---
sqlalchemy[asyncio]>=2.0.35
aiosqlite>=0.20.0
```
Chạy lệnh: `pip install -r requirements.txt`

---

### Bước 2: Xây dựng Database Models & Engine
1. Tạo `core/db/session.py`: Khởi tạo SQLAlchemy `async_sessionmaker` và `engine`.
2. Tạo `core/db/models.py`: Định nghĩa các bảng `User`, `TokenUsage`, `AuditLog`.
3. Tự động tạo bảng khi server khởi động (trong `lifespan` của `api/main.py`).

---

### Bước 3: Xây dựng LDAP Client Service
Tạo `core/auth/ldap_client.py` hỗ trợ 2 chế độ:
- **Production Mode**: Kết nối máy chủ LDAP thực tế, xác thực bằng tài khoản nhân viên và trích xuất `displayName`, `mail`, `department`, `memberOf`.
- **Mock/Dev Mode**: Cho phép test local khi không cắm mạng nội bộ PTSC hoặc chưa có kết nối Active Directory.

---

### Bước 4: Xây dựng JWT Handler & Password Utility
Tạo `core/auth/jwt_handler.py`:
- `create_access_token(data: dict, expires_delta)`
- `create_refresh_token(data: dict)`
- `decode_token(token: str) -> dict`

---

### Bước 5: Tạo FastAPI Security Dependencies
Tạo `core/auth/dependencies.py`:
- `get_current_user`: Trích xuất user từ header `Authorization: Bearer <token>`, kiểm tra trạng thái active trong DB.
- `require_roles(*roles)`: Chặn request nếu user không có quyền tương ứng.
- `check_user_quota`: Kiểm tra hạn mức chi phí AI của user trước khi gọi Agent.

---

### Bước 6: Xây dựng API Router cho Auth
Tạo `api/routers/auth.py`:
- `POST /api/v1/auth/login`: Nhận `{username, password}` ➔ Xác thực LDAP ➔ Upsert DB ➔ Trả JWT.
- `POST /api/v1/auth/refresh`: Cấp mới Access Token từ Refresh Token hợp lệ.
- `GET /api/v1/auth/me`: Trả về thông tin user hiện tại và hạn mức token.
- `POST /api/v1/auth/logout`: Xóa session / blacklist token.

---

### Bước 7: Bảo vệ các API Agent & Tích hợp Tracking
- Gắn `Depends(get_current_user)` vào endpoint của [Agent 0 Proofreader](file:///d:/PTSCQNG_AI_RESEARCH-/PAIP/agents/agent_0_proofreader/router.py).
- Sau khi LLM xử lý xong, tự động ghi số lượng token tiêu thụ vào bảng `token_usages`.

---

## 7. Các lưu ý quan trọng khi triển khai thực tế

1. **Chế độ Fake/Mock LDAP cho Dev**:
   - Khi dev ở nhà không có mạng VPN công ty, bật cờ `LDAP_MOCK_MODE=true` trong `.env` để giả lập xác thực thành công mà không cần máy chủ AD thật.
2. **Tài khoản Local Admin dự phòng**:
   - Khởi tạo sẵn tài khoản `admin_local` trong DB với mật khẩu mã hóa để đăng nhập khẩn cấp khi đường truyền AD gặp sự cố.
3. **Bảo mật Connection String & Secret Key**:
   - Luôn đưa `paip.db` và `.env` vào `.gitignore` để không bị lộ thông tin mật lên Git.
