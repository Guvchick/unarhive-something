from __future__ import annotations

import shutil

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import MAX_FILE_SIZE, LOCAL_API_URL
from utils.file_utils import human_size
from utils.stats import stats
from utils.video_utils import ffmpeg_available

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"🗜 <b>UnArchive Bot</b>\n\n"
        f"Привет, {name}! 👋\n\n"
        f"Отправь мне файл — остальное я сделаю сам:\n\n"
        f"📦 <b>Архивы</b>  →  разархивирую\n"
        f"   <code>ZIP · RAR · 7Z · TAR · GZ · BZ2 · XZ</code>\n\n"
        f"🖼 <b>Изображения</b>  →  конвертирую\n"
        f"   <code>JPG · PNG · WEBP · BMP · GIF · TIFF · ICO</code>\n\n"
        f"🎬 <b>Видео</b>  →  конвертирую\n"
        f"   <code>MP4 · AVI · MKV · MOV · WEBM · FLV</code>\n\n"
        f"<i>Максимальный размер файла: {human_size(MAX_FILE_SIZE)}</i>\n\n"
        f"📋 /help  •  📊 /stats  •  🔧 /status"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📋 <b>Справка</b>\n\n"
        "<b>Архивы (разархивация):</b>\n"
        "  .zip  .rar  .7z  .tar\n"
        "  .gz  .bz2  .xz  .tar.gz  .tar.bz2  .tar.xz\n\n"
        "<b>Изображения (конвертация):</b>\n"
        "  JPG ↔ PNG ↔ WEBP ↔ BMP ↔ GIF ↔ TIFF ↔ ICO\n\n"
        "<b>Видео (конвертация):</b>\n"
        "  MP4 ↔ AVI ↔ MKV ↔ MOV ↔ WEBM ↔ FLV\n\n"
        f"❗ Лимит: <b>{human_size(MAX_FILE_SIZE)}</b> на файл\n"
        "❗ Видеоконвертация требует <b>ffmpeg</b> на сервере"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    d = stats.snapshot
    total = d["archives_extracted"] + d["images_converted"] + d["videos_converted"]
    users = len(d["unique_users"])
    processed = human_size(d["bytes_processed"])

    await message.answer(
        "📊 <b>Статистика бота</b>\n\n"
        f"📦 Архивов распаковано:         <b>{d['archives_extracted']}</b>\n"
        f"🖼  Изображений сконвертировано: <b>{d['images_converted']}</b>\n"
        f"🎬 Видео сконвертировано:        <b>{d['videos_converted']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Всего обработано: <b>{total}</b>\n"
        f"📁 Объём данных:     <b>{processed}</b>\n"
        f"❌ Ошибок:           <b>{d['errors']}</b>\n"
        f"👥 Пользователей:    <b>{users}</b>\n\n"
        f"🕐 Запущен:  <code>{d['last_started_at']}</code>\n"
        f"🗓 Впервые:  <code>{d['first_started_at']}</code>"
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    ffmpeg_ok = ffmpeg_available()
    unrar_ok  = bool(shutil.which("unrar") or shutil.which("unrar-free"))

    lines = [
        f"{'✅' if ffmpeg_ok else '❌'} ffmpeg: {'доступен' if ffmpeg_ok else 'не найден'}",
        f"{'✅' if unrar_ok  else '⚠️'} unrar:  {'доступен' if unrar_ok  else 'не найден (RAR ограничен)'}",
    ]

    await message.answer(
        f"🟢 <b>Бот работает</b>\n\n"
        f"⏱ Аптайм: <b>{stats.uptime}</b>\n\n"
        + "\n".join(lines)
    )
