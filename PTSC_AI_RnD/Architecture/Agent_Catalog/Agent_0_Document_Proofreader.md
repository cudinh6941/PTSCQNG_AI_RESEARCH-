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
- Check theo chuẩn văn bản hành chính PTSC
- Check format (font, cỡ chữ, margin)
- Check thuật ngữ chuyên ngành (Oil & Gas)
- So sánh với template chuẩn

## Reuse
- **Xây nền tảng:** FastAPI + LLM Service + Document Reader
- **Các agent sau reuse:** Toàn bộ core infrastructure
