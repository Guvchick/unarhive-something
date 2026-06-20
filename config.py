from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int | None = int(os.getenv("ADMIN_ID", "0")) or None
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

for _d in (TEMP_DIR, LOGS_DIR, DATA_DIR):
    os.makedirs(_d, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB — Telegram bot upload limit

ARCHIVE_EXTENSIONS = frozenset({
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
})

IMAGE_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".ico",
})

IMAGE_FORMATS = ["jpg", "png", "webp", "bmp", "gif", "tiff", "ico"]

VIDEO_EXTENSIONS = frozenset({
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".ts",
})

VIDEO_FORMATS = ["mp4", "avi", "mkv", "mov", "webm", "flv"]
