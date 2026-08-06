"""
PAIP — FastAPI Application.

Entry point: uvicorn api.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from datetime import datetime

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.common.config import settings
from core.common.logger import logger
from core.common.schemas import HealthResponse

# Import agent routers
from agents.agent_0_proofreader.router import router as proofreader_router
from api.rules_router import router as rules_router
from core.rule_engine import rule_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events."""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.app_name} starting...")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   Default LLM: {settings.default_llm_provider}")
    logger.info(f"   Vault: {settings.obsidian_vault_path}")
    logger.info("=" * 60)

    # Khởi tạo Rule Engine (nạp từ điển & compile regex)
    rule_engine.load()

    yield
    logger.info(f"👋 {settings.app_name} shutting down...")


# ── App Instance ──────────────────────────────────────────

app = FastAPI(
    title="PAIP — PTSC AI Platform",
    description=(
        "AI Capability Platform nội bộ PTSC.\n\n"
        "Cung cấp các AI services có thể tái sử dụng:\n"
        "- **Agent 0**: Document Proofreader (kiểm tra chính tả)\n"
        "- **Agent 1**: Meeting Assistant (tóm tắt cuộc họp) — Coming soon\n"
        "- **Agent 2**: Requirement Reviewer — Coming soon\n"
        "- **Agent 3**: Procurement Assistant — Coming soon\n"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev only — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files & Web UI ─────────────────────────────────

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", tags=["Web UI"])
async def root():
    """Giao diện Web ứng dụng PAIP."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": f"Welcome to {settings.app_name}", "docs": "/docs"}


# ── Register Agent Routers ────────────────────────────────

app.include_router(proofreader_router)
app.include_router(rules_router)

# Future agents:
# from agents.agent_1_meeting.router import router as meeting_router
# app.include_router(meeting_router)


# ── Health Check ──────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version="0.1.0",
        environment=settings.app_env,
        timestamp=datetime.now(),
    )
