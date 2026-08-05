# 🗺️ Roadmap — PTSC AI R&D

## Solo Developer Timeline

```
Tuần 1-2     → Agent 0 — Document Proofreader     ← Xây core infrastructure
Tháng 1-2    → Agent 1 — Meeting Assistant         ← Quick win, demo ngay
Tháng 2-3    → Agent 2 — Requirement Reviewer      ← Reuse 70% từ Agent 0+1
Tháng 3-4    → Agent 3 — Procurement Assistant     ← Giá trị rõ cho mua sắm
Tháng 5-7    → Agent 4 — Knowledge Assistant       ← Xây RAG pipeline
Tháng 7-9    → Agent 5 — HSEQ Assistant            ← Reuse RAG từ Agent 4
Tháng 10+    → Agent 6 — IT Assistant              ← Chỉ khi có thêm người
```

## Development Phases

### Phase 1 — Research (Current)
- [ ] Pain Point Discovery
- [ ] AI Opportunity Mapping
- [ ] Capability Definition
- [ ] Phỏng vấn các phòng ban

### Phase 2 — Prototype
- [ ] POC cho Agent 0
- [ ] POC cho Agent 1
- [ ] Internal Demo

### Phase 3 — Pilot
- [ ] Triển khai thử 1 phòng ban
- [ ] Thu thập feedback
- [ ] Cải tiến

### Phase 4 — Production
- [ ] Enterprise Rollout
- [ ] Monitoring & Governance

## Kiến trúc chia sẻ

**Tất cả agents dùng chung:**
- FastAPI (backend)
- LLM Service (model router)
- Prompt Templates
- Response Parser
- Document Reader (Word/PDF) — xây từ Agent 0

**Agent 4 + 5 dùng thêm:**
- RAG Pipeline
- Vector Database
- Document Loader

> Agent 0 xây nền tảng → tất cả agent sau reuse
> Agent 1 xong → Agent 2-3 nhanh gấp đôi (reuse 70%)
> Agent 4 xong → Agent 5 reuse 60-70% RAG
