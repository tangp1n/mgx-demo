"""Logging infrastructure."""
import logging
import sys
from typing import Optional
from src.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

# Filter out noisy third-party loggers
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("appbuilder")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    if name:
        return logging.getLogger(f"appbuilder.{name}")
    return logger

