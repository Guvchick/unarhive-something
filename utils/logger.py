import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOGS_DIR, LOG_LEVEL

_R = "\033[0m"
_STYLES: dict[str, str] = {
    "DEBUG":    "\033[36m",
    "INFO":     "\033[32m",
    "WARNING":  "\033[33m",
    "ERROR":    "\033[31m",
    "CRITICAL": "\033[35;1m",
}
_GREY = "\033[90m"
_BLUE = "\033[94m"


class _ColorFormatter(logging.Formatter):
    _DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        c = _STYLES.get(record.levelname, "")
        fmt = (
            f"{_GREY}%(asctime)s{_R} "
            f"{c}%(levelname)-8s{_R} "
            f"{_BLUE}%(name)-22s{_R} "
            "%(message)s"
        )
        return logging.Formatter(fmt, datefmt=self._DATE_FMT).format(record)


def setup_logging() -> logging.Logger:
    level = getattr(logging, LOG_LEVEL, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    # ── Coloured console ──────────────────────────────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(_ColorFormatter())
    root.addHandler(ch)

    # ── Rotating file (plain text) ────────────────────────────────────────
    fh = RotatingFileHandler(
        os.path.join(LOGS_DIR, "bot.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)-22s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(fh)

    # ── Silence noisy third-party loggers ─────────────────────────────────
    for lib in ("aiogram.event", "aiohttp.access", "aiohttp.client"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    return logging.getLogger("bot")
