"""
Velora Centralized Logging Infrastructure.
Uses RotatingFileHandlers to prevent excessive log file accumulation and disk bloat.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import config

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

class Formatter(logging.Formatter):
    """Custom log formatter with clean output standard."""
    fmt = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(fmt=self.fmt, datefmt=self.datefmt)

import time

def cleanup_old_logs(max_age_days: int = 3):
    """Automated log cleaner removing log files older than max_age_days."""
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    for log_file in LOGS_DIR.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                print(f"[LogCleaner]: Removed expired log file '{log_file.name}'")
        except Exception as e:
            pass

def setup_logger(name: str, filename: str, level=None) -> logging.Logger:
    """Helper to set up rotating file and console handlers for a specific logger module."""
    if level is None:
        level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
        
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        # Rotating File Handler (Max 1MB per file, max 1 backup)
        file_handler = RotatingFileHandler(
            LOGS_DIR / filename,
            maxBytes=1 * 1024 * 1024,
            backupCount=1,
            encoding="utf-8"
        )
        file_handler.setFormatter(Formatter())
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(Formatter())
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    return logger

# Clean expired logs on logger initialization
cleanup_old_logs(max_age_days=3)


# Pre-instantiated specialized loggers
bot_logger = setup_logger("bot", "bot.log")
db_logger = setup_logger("db", "db.log")
error_logger = setup_logger("error", "errors.log", level=logging.ERROR)
admin_logger = setup_logger("admin", "admin.log")
market_logger = setup_logger("market", "market.log")
battle_logger = setup_logger("battle", "battles.log")
