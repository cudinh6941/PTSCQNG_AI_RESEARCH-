---
type: agent
agent_id: 2
name: Requirement Reviewer
difficulty: ⭐⭐⭐
solo_feasible: true
priority: 3
estimated_weeks: 3
status: Planning
serves_department: "Digital Transformation, Engineering"
linked_pain_points: 
linked_pocs: 
date_created: "2026-08-04"
---

# Agent 2 — Requirement Reviewer ✅

> **Ưu tiên: LÀM THỨ 3** — Reuse 70% code từ Agent 0+1.

## Workflow

### Input
Requirement document (Word / PDF)

### Processing
LLM kiểm tra theo các tiêu chí:
- **Business Rule** — Có đúng quy trình PTSC không?
- **Timeline** — Thời gian có hợp lý không?
- **Duplicate** — Có trùng requirement cũ không?
- **Logic** — Có mâu thuẫn nội bộ không?

### Output
- Báo cáo review
- Danh sách vấn đề
- Đề xuất chỉnh sửa

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | Python + FastAPI (reuse) |
| AI Model | LLM API |
| Database | PostgreSQL (lưu requirement cũ → check duplicate) |

## Ghi chú
- Reuse 70% code từ Agent 0+1
- Cần thu thập business rules thật của PTSC để nhúng vào prompt
