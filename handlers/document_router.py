from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import Message

from config import ARCHIVE_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS

router = Router(name="document_router")
log    = logging.getLogger("handler.document_router")


def _classify(filename: str) -> str:
    name = filename.lower()
    if name.endswith((".tar.gz", ".tar.bz2", ".tar.xz", ".tgz")):
        return "archive"
    ext = Path(name).suffix
    if ext in ARCHIVE_EXTENSIONS:
        return "archive"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


@router.message(F.document)
async def dispatch_document(message: Message, bot: Bot) -> None:
    doc  = message.document
    kind = _classify(doc.file_name)

    log.debug(
        "[%d] Document received: %s → %s",
        message.from_user.id, doc.file_name, kind,
    )

    if kind == "archive":
        from handlers.archive_handler import handle_archive
        await handle_archive(message, bot)

    elif kind == "image":
        from handlers.image_handler import handle_image_document
        await handle_image_document(message, bot)

    elif kind == "video":
        from handlers.video_handler import handle_video
        await handle_video(message, bot)

    else:
        log.info("[%d] Unknown file type: %s", message.from_user.id, doc.file_name)
        await message.reply(
            "❓ <b>Не знаю что делать с этим файлом</b>\n\n"
            "Отправь мне <b>архив</b>, <b>изображение</b> или <b>видео</b>.\n"
            "📋 /help — список поддерживаемых форматов"
        )
