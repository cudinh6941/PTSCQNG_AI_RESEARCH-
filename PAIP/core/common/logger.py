"""
PAIP Logger — structured logging with loguru.

Tất cả modules import logger từ đây:
    from core.common.logger import logger
"""

import sys
from pathlib import Path

from loguru import logger as _logger

from core.common.config import settings


def setup_logger() -> None:
    """Configure loguru logger."""
    # Remove default handler
    _logger.remove()

    # Console output (colorful, safe UTF-8 on Windows)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    _logger.add(
        sys.stdout,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File output (persistent)
    try:
        log_path = Path(settings.log_file)
        if not log_path.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent.parent
            log_path = base_dir / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        _logger.add(
            str(log_path),
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="30 days",
            encoding="utf-8",
        )
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to setup file logger: {e}\n")


# Auto-setup on import
setup_logger()

# Re-export
logger = _logger

