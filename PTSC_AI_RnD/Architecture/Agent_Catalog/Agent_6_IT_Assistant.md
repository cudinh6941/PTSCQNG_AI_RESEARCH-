---
type: agent
agent_id: 6
name: IT Assistant
difficulty: ⭐⭐⭐⭐⭐
solo_feasible: false
priority: 7
estimated_weeks: 8
status: Planning
serves_department: IT
linked_pain_points: 
linked_pocs: 
date_created: "2026-08-04"
---

# Agent 6 — IT Assistant ❌

> **Ưu tiên: CUỐI CÙNG** — Rủi ro bảo mật cao, cần thêm người.

## Workflow

### Input
Mô tả lỗi — Ví dụ: "Máy không join domain"

### Processing
AI phân tích → Sinh checklist → Sinh PowerShell script

### Output
- Checklist troubleshoot
- PowerShell commands
- Hướng dẫn fix

## ⚠️ CẢNH BÁO BẢO MẬT
> AI tự chạy PowerShell trên máy thật = RỦI RO BẢO MẬT CỰC LỚN
> Nếu AI hallucinate → chạy lệnh sai → hỏng hệ thống

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | Toàn bộ stack từ các agent trước |
| Security | Sandbox execution environment |
| Workflow | Approval flow trước khi chạy lệnh |
| Recovery | Rollback mechanism |

## Phased Approach
- **Phase 1:** CHỈ đưa ra hướng dẫn text, KHÔNG tự chạy lệnh
- **Phase 2:** Có thể tự chạy lệnh sau khi có approval flow + sandbox

## Ghi chú
- Cần thêm người review security trước khi triển khai
- KHÔNG NÊN ở giai đoạn đầu
