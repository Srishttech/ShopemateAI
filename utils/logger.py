"""
Centralized logging for ShopMate AI.

Logs the full trace required by the project spec:
- User Question
- Selected Tool
- Tool Output
- Final Response

All logs are written to logs/app.log and mirrored to the console.
"""

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes to logs/app.log and stdout."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(stream_handler)

        logger.propagate = False

    return logger
