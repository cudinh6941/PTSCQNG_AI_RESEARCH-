---
type: agent
agent_id: 5
name: HSEQ Assistant
difficulty: ⭐⭐⭐⭐
solo_feasible: true
priority: 6
estimated_weeks: 6
status: Planning
serves_department: HSEQ
linked_pain_points: 
linked_pocs: 
date_created: "2026-08-04"
---

# Agent 5 — HSEQ Assistant ⚠️

> **Ưu tiên: LÀM THỨ 6** — Reuse 60-70% RAG infrastructure từ Agent 4.

## Workflow

### Input
Upload tài liệu ISO

### Processing
AI đọc và phân tích ISO docs

### Output
- Checklist tuân thủ
- SOP (Standard Operating Procedure)
- Nội dung Training

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | Reuse RAG Pipeline từ Agent 4 |
| AI Model | LLM API với prompt chuyên biệt HSEQ |
| Libraries | OCR (nếu tài liệu ISO dạng scan) |

## Ghi chú
- Tái sử dụng 60-70% infrastructure từ Knowledge Assistant
- Tài liệu ISO thường dạng PDF scan → cần OCR trước
- Cần chuyên gia HSEQ review output
