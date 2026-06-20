from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any

from config import DATA_DIR

_FILE = os.path.join(DATA_DIR, "stats.json")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _uptime_str(since: datetime) -> str:
    secs = int((datetime.now(timezone.utc) - since).total_seconds())
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h} ч {m} мин"
    if m:
        return f"{m} мин {s} сек"
    return f"{s} сек"


class BotStats:
    _defaults: dict[str, Any] = {
        "first_started_at": "",
        "last_started_at": "",
        "archives_extracted": 0,
        "images_converted": 0,
        "videos_converted": 0,
        "bytes_processed": 0,
        "errors": 0,
        "unique_users": [],
        "total_requests": 0,
    }

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._d = self._load()
        self._session_start: datetime | None = None

    # ── Persistence ───────────────────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        if os.path.exists(_FILE):
            try:
                with open(_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in self._defaults.items():
                    data.setdefault(k, v)
                return data
            except Exception:
                pass
        d = dict(self._defaults)
        d["first_started_at"] = _now()
        return d

    def _save(self) -> None:
        try:
            with open(_FILE, "w", encoding="utf-8") as f:
                json.dump(self._d, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── Write API ─────────────────────────────────────────────────────────

    async def on_startup(self) -> None:
        async with self._lock:
            self._session_start = datetime.now(timezone.utc)
            self._d["last_started_at"] = _now()
            self._save()

    async def record(self, kind: str, user_id: int, size: int) -> None:
        """kind: 'archive' | 'image' | 'video'"""
        async with self._lock:
            suffix = "extracted" if kind == "archive" else "converted"
            self._d[f"{kind}s_{suffix}"] = self._d.get(f"{kind}s_{suffix}", 0) + 1
            self._d["bytes_processed"] += size
            self._d["total_requests"] += 1
            if user_id not in self._d["unique_users"]:
                self._d["unique_users"].append(user_id)
            self._save()

    async def record_error(self) -> None:
        async with self._lock:
            self._d["errors"] += 1
            self._save()

    # ── Read API ──────────────────────────────────────────────────────────

    @property
    def snapshot(self) -> dict[str, Any]:
        return dict(self._d)

    @property
    def uptime(self) -> str:
        if self._session_start is None:
            return "неизвестно"
        return _uptime_str(self._session_start)


stats = BotStats()
