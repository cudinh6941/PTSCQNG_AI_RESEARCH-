---
type: agent
agent_id: 4
name: Knowledge Assistant
difficulty: ⭐⭐⭐⭐
solo_feasible: true
priority: 5
estimated_weeks: 6
status: Planning
serves_department: Tất cả
linked_pain_points: 
linked_pocs: 
date_created: "2026-08-04"
---

# Agent 4 — Knowledge Assistant ⚠️

> **Ưu tiên: LÀM THỨ 5** — Enterprise RAG, bài toán phức tạp nhất.

## Workflow

### Input
Chat — Ví dụ: "Quy trình mua máy tính?"

### Processing
AI đọc tài liệu nội bộ (RAG) → Đọc SharePoint / uploaded documents

### Output
Trả lời dựa trên tài liệu thật

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | Python + FastAPI |
| AI Model | LLM API |
| Vector DB | pgvector hoặc Qdrant |
| RAG | Chunking + Embedding + Retrieval |
| Libraries | Document Loader (PDF, Word, Excel) |

## Phased Approach
- **Phase 1:** Upload file thủ công (không cần SharePoint connector)
- **Phase 2:** Tự động crawl SharePoint

## Ghi chú
- Đây là Enterprise RAG — bài toán phức tạp nhất
- Chất lượng phụ thuộc vào data ingestion
- Solo khả thi nhưng mất thời gian
