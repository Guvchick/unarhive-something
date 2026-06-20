from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, Message

from config import ARCHIVE_EXTENSIONS, MAX_FILE_SIZE
from utils.archive_utils import extract_archive, archive_type_label
from utils.file_utils import get_temp_path, get_unique_dir, cleanup, human_size, zip_directory
from utils.stats import stats

log = logging.getLogger("handler.archive")


def is_archive(filename: str) -> bool:
    name = filename.lower()
    if name.endswith((".tar.gz", ".tar.bz2", ".tar.xz", ".tgz")):
        return True
    return Path(name).suffix in ARCHIVE_EXTENSIONS


def _user(msg: Message) -> str:
    u = msg.from_user
    tag = f"@{u.username}" if u.username else u.first_name
    return f"[{u.id} {tag}]"


async def handle_archive(message: Message, bot: Bot) -> None:
    doc = message.document
    fname = doc.file_name
    fsize = doc.file_size

    if fsize > MAX_FILE_SIZE:
        await message.reply(
            f"❌ Файл слишком большой: <b>{human_size(fsize)}</b>\n"
            f"Максимум — 50 МБ."
        )
        return

    log.info("%s Received archive: %s (%s)", _user(message), fname, human_size(fsize))

    ext = "".join(Path(fname).suffixes[-2:]) if fname.lower().endswith(
        (".tar.gz", ".tar.bz2", ".tar.xz")
    ) else Path(fname).suffix
    archive_path = get_temp_path(ext=ext)
    extract_dir  = get_unique_dir()
    status_msg   = await message.reply("⏳ Скачиваю архив...")

    t0 = time.monotonic()
    try:
        await bot.download(doc, destination=archive_path)
        kind = archive_type_label(archive_path)

        await status_msg.edit_text(
            f"🔓 Распаковываю <code>{fname}</code>...\n"
            f"   📦 Формат: <b>{kind}</b>  •  📏 {human_size(fsize)}"
        )

        extracted = await asyncio.get_event_loop().run_in_executor(
            None, extract_archive, archive_path, extract_dir
        )

        if not extracted:
            await status_msg.edit_text("⚠️ Архив пуст.")
            return

        file_count = len(extracted)
        elapsed = time.monotonic() - t0

        if file_count == 1:
            single = extracted[0]
            out_name = Path(single).name
            result_size = os.path.getsize(single)
            await status_msg.edit_text(f"📤 Отправляю файл...")
            await message.reply_document(
                FSInputFile(single, filename=out_name),
                caption=(
                    f"✅ <b>Готово!</b>\n\n"
                    f"📦 <code>{fname}</code>\n"
                    f"📄 Извлечён: <code>{out_name}</code>\n"
                    f"📏 Размер: {human_size(result_size)}\n"
                    f"⏱ Время: {elapsed:.1f} с"
                ),
            )
        else:
            await status_msg.edit_text(f"🗜 Упаковываю {file_count} файлов в ZIP...")
            stem = Path(fname).stem.split(".")[0]
            out_zip = get_temp_path(ext=".zip")
            await asyncio.get_event_loop().run_in_executor(
                None, zip_directory, extract_dir, out_zip
            )
            zip_size = os.path.getsize(out_zip)
            elapsed = time.monotonic() - t0

            await status_msg.edit_text(f"📤 Отправляю архив с результатами...")
            await message.reply_document(
                FSInputFile(out_zip, filename=f"{stem}_extracted.zip"),
                caption=(
                    f"✅ <b>Готово!</b>\n\n"
                    f"📦 <code>{fname}</code>\n"
                    f"📄 Файлов извлечено: <b>{file_count}</b>\n"
                    f"📏 Размер результата: {human_size(zip_size)}\n"
                    f"⏱ Время: {elapsed:.1f} с"
                ),
            )
            cleanup(out_zip)

        await status_msg.delete()
        await stats.record("archive", message.from_user.id, fsize)
        log.info(
            "%s Done: extracted %d file(s) from %s in %.1fs",
            _user(message), file_count, fname, elapsed,
        )

    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("%s Error extracting %s after %.1fs: %s", _user(message), fname, elapsed, exc)
        await stats.record_error()
        await status_msg.edit_text(
            f"❌ <b>Не удалось распаковать архив</b>\n\n"
            f"<code>{exc}</code>\n\n"
            f"💡 Проверь, что файл не повреждён и не защищён паролем."
        )
    finally:
        cleanup(archive_path, extract_dir)
