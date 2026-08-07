---
type: agent
agent_id: 0
name: Document Proofreader
difficulty: ⭐
solo_feasible: true
priority: -1
estimated_weeks: 2
status: In Progress
serves_department: Tất cả
linked_pain_points: "[[PP_003_Loi_chinh_ta_van_ban]]"
linked_pocs:
code_path: d:/AI_R&D/PAIP/agents/agent_0_proofreader/
date_created: 2026-08-04
---

# Agent 0 — Document Proofreader ✅

> **Ưu tiên: LÀM ĐẦU TIÊN** — Đơn giản nhất, xây core infrastructure cho các agent sau.
> 
> **Code:** `d:/AI_R&D/PAIP/agents/agent_0_proofreader/`
> **API:** `POST /api/v1/proofread/text` | `POST /api/v1/proofread/file`

## Workflow

### Input
Upload hồ sơ (Word / PDF) hoặc paste text trực tiếp

### Processing
Đọc nội dung file → LLM kiểm tra chính tả, ngữ pháp, cách dùng từ
	Chungking? 
### Output
- Danh sách lỗi chính tả
- Danh sách lỗi ngữ pháp
- Gợi ý sửa cho từng lỗi
- Mức độ nghiêm trọng (low/medium/high)
- Điểm chất lượng văn bản (1-10)

## Tech Stack

| Thành phần | Công nghệ                | Code                                    |
| ---------- | ------------------------ | --------------------------------------- |
| Backend    | Python + FastAPI         | `api/main.py`                           |
| AI Model   | OpenAI / Gemini / Claude | `core/llm/service.py`                   |
| Doc Reader | python-docx, pdfplumber  | `core/document/reader.py`               |
| Prompts    | Vietnamese proofreading  | `agents/agent_0_proofreader/prompts.py` |

## API Endpoints

| Method | Path | Mô tả |
|---|---|---|
| POST | `/api/v1/proofread/text` | Kiểm tra text trực tiếp |
| POST | `/api/v1/proofread/file` | Upload file Word/PDF |

## Tại sao làm đầu tiên?

- Đơn giản nhất trong tất cả agents
- Ai cũng viết hồ sơ → impact cực lớn
- Demo cực nhanh: upload file → nhận lỗi ngay
- Không cần database, không cần RAG
- **Xây dựng được core infrastructure (FastAPI + LLM Service) cho các agent sau**

## Mở rộng tương lai
- ✅ Tích hợp Rule Engine & Từ điển chuyên ngành (Glossary) — **Đã hoàn thành**
- ✅ Tích hợp Database (SQLite/PostgreSQL) — **Đã hoàn thành**
- 🔜 Check tính nhất quán văn bản (Consistency Check): Đối soát số hiệu, số tiền, ngày tháng, tên đối tác — Xem [[Consistency_Check_Architecture]]
- 🔜 Check thể thức & định dạng theo chuẩn Nghị định 30/2020/NĐ-CP (Căn lề, Font Times New Roman, Cỡ chữ, Căn đều Justified, 1-Click Auto-Format) — Xem [[Format_Inspection_Architecture]]
- 🔜 So sánh với template chuẩn

## Chế độ Kiểm tra (Modes)

| Mode | Tên | Mục tiêu |
|---|---|---|
| `standard` | Tiêu chuẩn | Chính tả, dấu thanh, phụ âm, dấu câu |
| `formal` | Trang trọng / Công văn | Thể thức NĐ30, văn phong hành chính chuẩn mực |
| `strict` | Pháp lý & Số liệu | Đối chiếu số tiền số/chữ, tính nhất quán điều khoản |
| `legal` | Thẩm định Pháp lý | Tra cứu luật thời gian thực (Google Search Grounding) |

## Reuse
- **Xây nền tảng:** FastAPI + LLM Service + Document Reader + Rule Engine + Database
- **Các agent sau reuse:** Toàn bộ core infrastructure
