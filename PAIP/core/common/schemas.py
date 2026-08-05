"""
PAIP Base Schemas — shared data models.

Tất cả agents kế thừa từ các schemas này.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    MOCK = "mock"


class AIRequest(BaseModel):
    """Base request model for all AI operations."""
    user_id: str | None = Field(default=None, description="ID người dùng")
    department: str | None = Field(default=None, description="Phòng ban")
    provider: LLMProvider | None = Field(default=None, description="LLM provider (nếu muốn override default)")
    model: str | None = Field(default=None, description="Model cụ thể (nếu muốn override default)")


class AIResponse(BaseModel):
    """Base response model for all AI operations."""
    success: bool = Field(description="Kết quả xử lý")
    message: str = Field(default="", description="Thông báo")
    processing_time_ms: float = Field(default=0.0, description="Thời gian xử lý (ms)")
    model_used: str = Field(default="", description="Model đã dùng")
    tokens_used: int = Field(default=0, description="Số tokens đã dùng")
    estimated_cost_usd: float = Field(default=0.0, description="Chi phí ước tính (USD)")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    app_name: str = "PAIP"
    version: str = "0.1.0"
    environment: str = "development"
    timestamp: datetime = Field(default_factory=datetime.now)

