from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import VIDEO_EXTENSIONS, VIDEO_FORMATS, MAX_FILE_SIZE
from utils.file_utils import get_temp_path, cleanup, human_size
from utils.video_utils import convert_video, get_video_info, ffmpeg_available
from utils.stats import stats

router = Router(name="video")
log    = logging.getLogger("handler.video")

# user_id → {path, original_ext}
_pending: dict[int, dict] = {}


def is_video(filename: str) -> bool:
    return Path(filename.lower()).suffix in VIDEO_EXTENSIONS


def _user_tag(msg: Message) -> str:
    u = msg.from_user
    return f"[{u.id} {'@'+u.username if u.username else u.first_name}]"


def _video_keyboard(exclude_ext: str) -> object:
    cur = exclude_ext.lower().lstrip(".")
    builder = InlineKeyboardBuilder()
    for fmt in VIDEO_FORMATS:
        if fmt != cur:
            builder.button(text=fmt.upper(), callback_data=f"vid:{fmt}")
    builder.button(text="❌ Отмена", callback_data="vid:cancel")
    builder.adjust(3)
    return builder.as_markup()


def _fmt_duration(secs: float) -> str:
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


@router.message(F.video)
async def handle_video_message(message: Message, bot: Bot) -> None:
    await handle_video(message, bot)


async def handle_video(message: Message, bot: Bot) -> None:
    if not ffmpeg_available():
        # Only respond if we're sure it's a video
        if message.video or (message.document and is_video(message.document.file_name)):
            await message.reply(
                "❌ <b>ffmpeg не установлен</b>\n\n"
                "Конвертация видео недоступна на этом сервере.\n"
                "Попроси администратора установить ffmpeg."
            )
        return

    if message.video:
        file_obj = message.video
        fname    = message.video.file_name or "video.mp4"
        ext      = Path(fname).suffix.lower() or ".mp4"
        fsize    = message.video.file_size or 0
    elif message.document:
        file_obj = message.document
        fname    = message.document.file_name
        ext      = Path(fname).suffix.lower()
        fsize    = message.document.file_size or 0
    else:
        return

    if fsize > MAX_FILE_SIZE:
        await message.reply(
            f"❌ Файл слишком большой: <b>{human_size(fsize)}</b>\n"
            f"Максимум — 50 МБ."
        )
        return

    log.info("%s Received video: %s (%s)", _user_tag(message), fname, human_size(fsize))
    status = await message.reply(f"⏳ Скачиваю <code>{fname}</code>...")
    src = get_temp_path(ext=ext)

    try:
        await bot.download(file_obj, destination=src)
        info = await asyncio.get_event_loop().run_in_executor(None, get_video_info, src)

        cur_ext = ext.lstrip(".")
        _pending[message.from_user.id] = {"path": src, "ext": cur_ext}

        meta_lines = [f"🎬 <b>{fname}</b>"]
        if info.get("width"):
            meta_lines.append(f"📐 Разрешение: <b>{info['width']}×{info['height']}</b>")
        if info.get("duration"):
            meta_lines.append(f"🕐 Длительность: <b>{_fmt_duration(info['duration'])}</b>")
        if info.get("codec"):
            meta_lines.append(f"🔧 Кодек: <code>{info['codec']}</code>")
        meta_lines.append(f"📏 Размер: {human_size(fsize)}")
        meta_lines.append("")
        meta_lines.append("Выбери <b>формат конвертации</b>:")

        await status.edit_text(
            "\n".join(meta_lines),
            reply_markup=_video_keyboard(cur_ext),
        )
    except Exception as exc:
        log.error("%s Video download error: %s", _user_tag(message), exc)
        cleanup(src)
        await status.edit_text(f"❌ Ошибка при скачивании:\n<code>{exc}</code>")


@router.callback_query(F.data.startswith("vid:"))
async def handle_format_choice(callback: CallbackQuery) -> None:
    target = callback.data.split(":")[1]
    uid    = callback.from_user.id

    if target == "cancel":
        pending = _pending.pop(uid, None)
        if pending:
            cleanup(pending["path"])
        await callback.message.edit_text("❌ Отменено.")
        await callback.answer()
        return

    pending = _pending.pop(uid, None)
    if not pending:
        await callback.answer("⚠️ Файл не найден. Отправь видео заново.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(
        f"⚙️ Конвертирую в <b>{target.upper()}</b>...\n"
        f"<i>Это может занять несколько минут</i>"
    )

    src = pending["path"]
    dst = get_temp_path(ext=f".{target}")
    t0  = time.monotonic()

    try:
        await asyncio.get_event_loop().run_in_executor(
            None, convert_video, src, dst, target
        )
        elapsed = time.monotonic() - t0
        result_size = os.path.getsize(dst)

        await callback.message.reply_document(
            FSInputFile(dst, filename=f"converted.{target}"),
            caption=(
                f"✅ <b>Готово!</b>\n\n"
                f"🎬 Формат: <b>{pending['ext'].upper()} → {target.upper()}</b>\n"
                f"📏 Размер: {human_size(result_size)}\n"
                f"⏱ Время: {elapsed:.0f} с"
            ),
        )
        await callback.message.delete()
        await stats.record("video", uid, os.path.getsize(src))
        log.info(
            "[%d] Video converted: %s → %s in %.0fs",
            uid, pending["ext"], target, elapsed,
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("[%d] Video conversion error after %.0fs: %s", uid, elapsed, exc)
        await stats.record_error()
        await callback.message.edit_text(
            f"❌ <b>Не удалось конвертировать</b>\n\n"
            f"<code>{exc}</code>"
        )
    finally:
        cleanup(src, dst)
