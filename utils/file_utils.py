from __future__ import annotations

import os
import shutil
import uuid
import zipfile

from config import TEMP_DIR


def get_temp_path(ext: str = "") -> str:
    return os.path.join(TEMP_DIR, f"{uuid.uuid4()}{ext}")


def get_unique_dir() -> str:
    path = os.path.join(TEMP_DIR, str(uuid.uuid4()))
    os.makedirs(path, exist_ok=True)
    return path


def cleanup(*paths: str) -> None:
    for p in paths:
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass


def cleanup_temp_dir() -> int:
    """Remove all leftover files from previous sessions. Returns count removed."""
    removed = 0
    for entry in os.scandir(TEMP_DIR):
        try:
            if entry.is_file():
                os.remove(entry.path)
            elif entry.is_dir():
                shutil.rmtree(entry.path)
            removed += 1
        except Exception:
            pass
    return removed


def human_size(size_bytes: int) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} ТБ"


def zip_directory(src_dir: str, out_path: str) -> str:
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                zf.write(abs_path, os.path.relpath(abs_path, src_dir))
    return out_path
