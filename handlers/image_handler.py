from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import IMAGE_EXTENSIONS, IMAGE_FORMATS, MAX_FILE_SIZE
from utils.file_utils import get_temp_path, cleanup, human_size
from utils.image_utils import convert_image, get_image_info
from utils.stats import stats

router = Router(name="image")
log    = logging.getLogger("handler.image")

# user_id → {path, original_ext}
_pending: dict[int, dict] = {}


def is_image(filename: str) -> bool:
    return Path(filename.lower()).suffix in IMAGE_EXTENSIONS


def _user(msg: Message) -> str:
    u = msg.from_user
    return f"[{u.id} {'@'+u.username if u.username else u.first_name}]"


def _format_keyboard(exclude_ext: str) -> object:
    cur = exclude_ext.lower().lstrip(".").replace("jpeg", "jpg")
    builder = InlineKeyboardBuilder()
    for fmt in IMAGE_FORMATS:
        if fmt != cur:
            builder.button(text=fmt.upper(), callback_data=f"img:{fmt}")
    builder.button(text="❌ Отмена", callback_data="img:cancel")
    builder.adjust(4)
    return builder.as_markup()


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    photo = message.photo[-1]
    log.info("%s Received photo (%.0f KB)", _user(message), (photo.file_size or 0) / 1024)
    status = await message.reply("⏳ Скачиваю фото...")
    src = get_temp_path(ext=".jpg")
    try:
        await bot.download(photo, destination=src)
        info = await asyncio.get_event_loop().run_in_executor(None, get_image_info, src)
        _pending[message.from_user.id] = {"path": src, "ext": "jpg"}
        await status.edit_text(
            f"🖼 <b>Фото получено</b>\n\n"
            f"📐 Размер: <b>{info['width']}×{info['height']} px</b>\n"
            f"📏 Файл: {human_size(photo.file_size or 0)}\n\n"
            f"Выбери <b>формат конвертации</b>:",
            reply_markup=_format_keyboard("jpg"),
        )
    except Exception as exc:
        log.error("%s Photo download error: %s", _user(message), exc)
        cleanup(src)
        await status.edit_text(f"❌ Ошибка при скачивании:\n<code>{exc}</code>")


async def handle_image_document(message: Message, bot: Bot) -> None:
    doc  = message.document
    fname = doc.file_name
    fsize = doc.file_size

    if fsize > MAX_FILE_SIZE:
        await message.reply(
            f"❌ Файл слишком большой: <b>{human_size(fsize)}</b>\n"
            f"Максимум — 50 МБ."
        )
        return

    log.info("%s Received image: %s (%s)", _user(message), fname, human_size(fsize))
    ext = Path(fname).suffix.lower()
    status = await message.reply(f"⏳ Скачиваю {fname}...")
    src = get_temp_path(ext=ext)
    try:
        await bot.download(doc, destination=src)
        info = await asyncio.get_event_loop().run_in_executor(None, get_image_info, src)
        orig_ext = ext.lstrip(".")
        _pending[message.from_user.id] = {"path": src, "ext": orig_ext}
        await status.edit_text(
            f"🖼 <b>{fname}</b>\n\n"
            f"📐 Размер: <b>{info['width']}×{info['height']} px</b>\n"
            f"🎨 Режим: <code>{info['mode']}</code>  •  📏 {human_size(fsize)}\n\n"
            f"Выбери <b>формат конвертации</b>:",
            reply_markup=_format_keyboard(orig_ext),
        )
    except Exception as exc:
        log.error("%s Image download error: %s", _user(message), exc)
        cleanup(src)
        await status.edit_text(f"❌ Ошибка при скачивании:\n<code>{exc}</code>")


@router.callback_query(F.data.startswith("img:"))
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
        await callback.answer("⚠️ Файл не найден. Отправь изображение заново.", show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(f"⚙️ Конвертирую в <b>{target.upper()}</b>...")

    src = pending["path"]
    dst = get_temp_path(ext=f".{target}")
    t0  = time.monotonic()

    try:
        await asyncio.get_event_loop().run_in_executor(
            None, convert_image, src, dst, target
        )
        elapsed = time.monotonic() - t0
        result_size = os.path.getsize(dst)

        await callback.message.reply_document(
            FSInputFile(dst, filename=f"converted.{target}"),
            caption=(
                f"✅ <b>Готово!</b>\n\n"
                f"🖼 Формат: <b>{pending['ext'].upper()} → {target.upper()}</b>\n"
                f"📏 Размер: {human_size(result_size)}\n"
                f"⏱ Время: {elapsed:.1f} с"
            ),
        )
        await callback.message.delete()
        await stats.record("image", uid, os.path.getsize(src))
        log.info(
            "[%d] Image converted: %s → %s in %.1fs",
            uid, pending["ext"], target, elapsed,
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        log.error("[%d] Image conversion error after %.1fs: %s", uid, elapsed, exc)
        await stats.record_error()
        await callback.message.edit_text(
            f"❌ <b>Не удалось конвертировать</b>\n\n"
            f"<code>{exc}</code>"
        )
    finally:
        cleanup(src, dst)
