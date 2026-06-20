from __future__ import annotations

import gzip
import bz2
import lzma
import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Optional


def detect_archive_type(path: str) -> Optional[str]:
    name = Path(path).name.lower()
    for suffix in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if name.endswith(suffix):
            return suffix[1:]  # ".tar.gz" → "tar.gz"
    if name.endswith(".tgz"):
        return "tar.gz"
    return {
        ".zip": "zip",
        ".tar": "tar",
        ".gz":  "gz",
        ".bz2": "bz2",
        ".xz":  "xz",
        ".7z":  "7z",
        ".rar": "rar",
    }.get(Path(path).suffix.lower())


def _setup_rarfile() -> None:
    import rarfile
    for tool in ("unrar", "unrar-free", "bsdtar"):
        if shutil.which(tool):
            rarfile.UNRAR_TOOL = tool
            return


def extract_archive(archive_path: str, extract_dir: str) -> list[str]:
    kind = detect_archive_type(archive_path)
    if kind is None:
        raise ValueError("Неподдерживаемый формат архива")

    if kind == "zip":
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_dir)

    elif kind.startswith("tar"):
        mode_map = {
            "tar":      "r:",
            "tar.gz":   "r:gz",
            "tar.bz2":  "r:bz2",
            "tar.xz":   "r:xz",
        }
        with tarfile.open(archive_path, mode_map.get(kind, "r:*")) as tf:
            tf.extractall(extract_dir)

    elif kind == "gz":
        out_path = os.path.join(extract_dir, Path(archive_path).stem)
        with gzip.open(archive_path, "rb") as gf, open(out_path, "wb") as out:
            shutil.copyfileobj(gf, out)

    elif kind == "bz2":
        out_path = os.path.join(extract_dir, Path(archive_path).stem)
        with bz2.open(archive_path, "rb") as bf, open(out_path, "wb") as out:
            shutil.copyfileobj(bf, out)

    elif kind == "xz":
        out_path = os.path.join(extract_dir, Path(archive_path).stem)
        with lzma.open(archive_path, "rb") as lf, open(out_path, "wb") as out:
            shutil.copyfileobj(lf, out)

    elif kind == "7z":
        import py7zr
        with py7zr.SevenZipFile(archive_path, mode="r") as sz:
            sz.extractall(path=extract_dir)

    elif kind == "rar":
        _setup_rarfile()
        import rarfile
        with rarfile.RarFile(archive_path) as rf:
            rf.extractall(extract_dir)

    # Collect all extracted files
    extracted: list[str] = []
    for root, _, files in os.walk(extract_dir):
        for f in files:
            extracted.append(os.path.join(root, f))
    return extracted


def archive_type_label(path: str) -> str:
    kind = detect_archive_type(path)
    return (kind or "unknown").upper()
