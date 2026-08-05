# 🏛️ PAIP — PTSC AI Platform Architecture

> Version: 1.0 | Status: R&D | Author: PTSC Digital Transformation Team

---

## Vision

PTSC AI Platform là nền tảng AI nội bộ được xây dựng nhằm chuẩn hóa, tái sử dụng và mở rộng các năng lực AI phục vụ hoạt động sản xuất, vận hành và chuyển đổi số của PTSC.

- Đây **KHÔNG** phải là một chatbot
- Đây **KHÔNG** phải là một ChatGPT clone  
- Đây là một **AI Capability Platform**

Mục tiêu: xây dựng các AI Capabilities có thể tái sử dụng giữa HSEQ, Procurement, IT, HR, Finance, Engineering, Digital Transformation.

---

## Core Philosophy

Không phát triển AI vì AI. Chỉ phát triển AI khi:
- Giải quyết pain point rõ ràng
- Tiết kiệm thời gian
- Giảm thao tác lặp lại
- Tăng độ chính xác
- Tăng tốc ra quyết định

> **Mọi AI đều phải đo được ROI.**

---

## Product Principles

1. **Microsoft 365 First** — Nếu M365 đã có khả năng phù hợp thì ưu tiên tận dụng
2. **AI Capability First** — Không phát triển chatbot riêng cho từng phòng ban, phát triển reusable capabilities
3. **API First** — Toàn bộ AI Service expose API (Web, Power Automate, Teams, SharePoint, Mobile)
4. **Vendor Agnostic** — Có thể swap OpenAI ↔ Gemini ↔ Claude ↔ Azure ↔ Local LLM mà không đổi logic
5. **Human-in-the-loop** — AI chỉ hỗ trợ, con người phê duyệt cuối cùng

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Client Layer                   │
│  Web Portal │ Teams │ Power Apps │ Mobile │ ...  │
├─────────────────────────────────────────────────┤
│              Authentication Layer               │
│            Microsoft Entra ID                   │
├─────────────────────────────────────────────────┤
│              API Gateway Layer                  │
│  REST API │ Auth │ Logging │ Rate Limit │ Route │
├─────────────────────────────────────────────────┤
│           AI Orchestration Layer                │
│  Prompt Builder │ Context │ Memory │ Router     │
│  Cost Controller │ Response Validator           │
├─────────────────────────────────────────────────┤
│            AI Capability Layer                  │
│  Meeting │ Requirement │ Knowledge │ HSEQ       │
│  Procurement │ Document │ Translation │ OCR     │
├─────────────────────────────────────────────────┤
│           Knowledge & Data Layer                │
│  SharePoint │ OneDrive │ SQL │ PDF │ SOP │ ISO  │
├─────────────────────────────────────────────────┤
│             AI Provider Layer                   │
│  OpenAI │ Gemini │ Claude │ Azure │ Ollama      │
└─────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | NestJS, Python, FastAPI |
| Frontend | React, Next.js (if needed) |
| Database | PostgreSQL, Redis, Vector DB (future) |
| Infrastructure | Docker, M365, Power Automate, Power BI |
| Cloud | Azure (preferred), Local VM (dev) |

---

## AI Agent Catalog

> Chi tiết từng Agent xem trong folder [[Agent_Catalog]]

| Agent | Tên | Độ khó | Solo? | Ưu tiên |
|---|---|---|---|---|
| 0 | [[Agent_0_Document_Proofreader]] | ⭐ | ✅ | Làm đầu tiên |
| 1 | [[Agent_1_Meeting_Assistant]] | ⭐⭐ | ✅ | Thứ 2 |
| 2 | [[Agent_2_Requirement_Reviewer]] | ⭐⭐⭐ | ✅ | Thứ 3 |
| 3 | [[Agent_3_Procurement_Assistant]] | ⭐⭐⭐ | ✅ | Thứ 4 |
| 4 | [[Agent_4_Knowledge_Assistant]] | ⭐⭐⭐⭐ | ⚠️ | Thứ 5 |
| 5 | [[Agent_5_HSEQ_Assistant]] | ⭐⭐⭐⭐ | ⚠️ | Thứ 6 |
| 6 | [[Agent_6_IT_Assistant]] | ⭐⭐⭐⭐⭐ | ❌ | Cuối cùng |

---

## Governance & Security

- **Auth:** Microsoft Entra ID
- **Authorization:** Role-based Access Control
- **Logging:** Timestamp, User, Department, Capability, Model, Token, Latency, Cost, Status
- **Encryption:** HTTPS
- **Secrets:** Environment Variables (không hardcode API Keys)

---

## Mission Statement

PAIP không nhằm thay thế con người. PAIP được xây dựng để:
- Giảm công việc lặp lại
- Hỗ trợ ra quyết định
- Khai thác tri thức doanh nghiệp
- Thúc đẩy chuyển đổi số
- Tạo nền tảng AI thống nhất cho PTSC
