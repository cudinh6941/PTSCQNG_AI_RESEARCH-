---
type: agent
agent_id: 3
name: Procurement Assistant
difficulty: ⭐⭐⭐
solo_feasible: true
priority: 4
estimated_weeks: 4
status: Planning
serves_department: Procurement
linked_pain_points: 
linked_pocs: 
date_created: "2026-08-04"
---

# Agent 3 — Procurement Assistant ✅

> **Ưu tiên: LÀM THỨ 4** — Giá trị rõ cho bộ phận mua sắm.

## Workflow

### Input
Upload báo giá (PDF / Excel)

### Processing
Parse file → Extract data → LLM so sánh

### Output
- So sánh giá giữa các vendor
- Highlight chênh lệch
- Sinh hồ sơ đề xuất

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | Python + FastAPI |
| AI Model | LLM API |
| Libraries | PyPDF2, pdfplumber, openpyxl |

## Ghi chú
- Giá trị rõ ràng cho bộ phận mua sắm
- Cần template hồ sơ đề xuất mẫu của PTSC
