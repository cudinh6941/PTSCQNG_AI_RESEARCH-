---
type: agent
agent_id: 1
name: Meeting Assistant
difficulty: ⭐⭐
solo_feasible: true
priority: 2
estimated_weeks: 3
status: Planning
serves_department: Tất cả
linked_pain_points: 
linked_pocs: 
date_created: "2026-08-04"
---

# Agent 1 — Meeting Assistant ✅

> **Ưu tiên: LÀM THỨ 2** — Quick win, demo cho lãnh đạo ngay.

## Workflow

### Input
Meeting Transcript (text hoặc file ghi âm)

### Processing
1. Speech-to-Text (Whisper API nếu input là audio)
2. LLM xử lý transcript

### Output
- **Minutes** — Biên bản họp
- **Decisions** — Quyết định
- **Tasks** — Công việc được giao
- **Requirements** — Yêu cầu phát sinh
- **Email** — Email tóm tắt gửi stakeholders

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | Python + FastAPI |
| AI Model | OpenAI / Gemini / Claude |
| Speech-to-Text | Whisper API |

## Tại sao ưu tiên cao?
- Ai cũng họp → impact lớn, dễ thấy giá trị
- Input/Output rõ ràng
- Không cần database phức tạp
- Demo được cho ban lãnh đạo ngay

## Reuse
- **Từ Agent 0:** FastAPI + LLM Service
- **Cho Agent sau:** Response Parser, Prompt Templates
