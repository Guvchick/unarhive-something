from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int | None = int(os.getenv("ADMIN_ID", "0")) or None
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Local Telegram Bot API server URL (set via docker-compose environment).
# When set, file limit rises to 2 GB. Empty = use Telegram's public API (50 MB).
LOCAL_API_URL: str = os.getenv("LOCAL_API_URL", "").rstrip("/")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")

for _d in (TEMP_DIR, LOGS_DIR, DATA_DIR):
    os.makedirs(_d, exist_ok=True)

# 1 GB when local API is available, else 50 MB (public API hard limit)
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024 if LOCAL_API_URL else 50 * 1024 * 1024

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
