# PAIP — PTSC AI Platform

> AI Capability Platform nội bộ PTSC.  
> Spec & Design: `../PTSC_AI_RnD/` (Obsidian Vault)

## Quick Start

```bash
# 1. Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Copy và chỉnh sửa config
copy .env.example .env
# Sửa .env → thêm API keys

# 4. Chạy dev server
uvicorn api.main:app --reload --port 8000
```

## Cấu trúc

```
PAIP/
├── core/               ← Shared infrastructure (dùng chung cho mọi agent)
│   ├── llm/            ← LLM Service — gọi OpenAI/Gemini/Claude
│   ├── document/       ← Document Reader — đọc Word/PDF
│   └── common/         ← Config, Logger, Base schemas
├── agents/             ← Mỗi agent = 1 module độc lập
│   └── agent_0_proofreader/
├── api/                ← FastAPI application
├── tests/              ← Test suite
└── scripts/            ← Utility scripts
```

## Liên kết với Obsidian Vault

| Obsidian (Design) | Code (Build) |
|---|---|
| `Architecture/Agent_Catalog/Agent_0_*.md` | `agents/agent_0_proofreader/` |
| `Lab&Research/Prompts/Prompt_*.md` | `agents/*/prompts.py` |
| `Lab&Research/POC/POC_*.md` (test cases) | `tests/` |
| `Architecture/PAIP_Architecture.md` | Cấu trúc tổng thể |

## API Docs

Sau khi chạy server: http://localhost:8000/docs
