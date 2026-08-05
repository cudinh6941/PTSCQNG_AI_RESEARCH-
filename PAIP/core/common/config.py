"""
PAIP Configuration — đọc từ .env file.

Tất cả settings tập trung ở đây, không hardcode ở bất kỳ đâu khác.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", str(_ENV_PATH)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "PAIP"
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    # --- Obsidian Vault ---
    obsidian_vault_path: str = "d:/AI_R&D/PTSC_AI_RnD"

    # --- LLM Providers ---
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o-mini"

    google_api_key: str = ""
    gemini_default_model: str = "gemini-2.5-flash"

    anthropic_api_key: str = ""
    claude_default_model: str = "claude-sonnet-4-20250514"

    default_llm_provider: str = "gemini"

    # --- Cost Control ---
    monthly_cost_limit_usd: float = 50.0
    alert_threshold_usd: float = 40.0

    # --- Logging ---
    log_level: str = "INFO"
    log_file: str = "logs/paip.log"

    @property
    def vault_path(self) -> Path:
        """Return Obsidian vault path as Path object."""
        return Path(self.obsidian_vault_path)

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


# Singleton instance
settings = Settings()

