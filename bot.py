from __future__ import annotations

import asyncio
import platform
import shutil
from datetime import datetime, timezone

from aiohttp import ClientTimeout
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_ID, LOCAL_API_URL, MAX_FILE_SIZE
from utils.logger import setup_logging
from utils.stats import stats
from utils.file_utils import cleanup_temp_dir, human_size
from utils.video_utils import ffmpeg_available

log = setup_logging()


def _make_bot() -> Bot:
    props = DefaultBotProperties(parse_mode=ParseMode.HTML)

    if LOCAL_API_URL:
        session = AiohttpSession(
            api=TelegramAPIServer.from_base(LOCAL_API_URL, is_local=True),
            # No hard timeout — 1 GB file at local-disk speeds still takes time
            timeout=ClientTimeout(total=None, connect=10),
        )
        return Bot(token=BOT_TOKEN, session=session, default=props)

    return Bot(token=BOT_TOKEN, default=props)


def _box(lines: list[str], width: int = 62) -> str:
    bar = "─" * width
    rows = "\n".join(f"│  {ln:<{width - 4}}│" for ln in lines)
    return f"┌{bar}┐\n{rows}\n└{bar}┘"


async def _on_startup(bot: Bot) -> None:
    removed = cleanup_temp_dir()
    if removed:
        log.info("Cleaned up %d leftover temp file(s) from previous session", removed)

    await stats.on_startup()

    me         = await bot.get_me()
    ffmpeg_ok  = ffmpeg_available()
    unrar_ok   = bool(shutil.which("unrar") or shutil.which("unrar-free"))
    local_api  = bool(LOCAL_API_URL)
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    banner_lines = [
        f"Bot       : @{me.username}  (ID {me.id})",
        f"Name      : {me.full_name}",
        "",
        f"API mode  : {'LOCAL — ' + LOCAL_API_URL if local_api else 'PUBLIC (api.telegram.org)'}",
        f"File limit: {human_size(MAX_FILE_SIZE)}",
        "",
        f"ffmpeg    : {'✓ available' if ffmpeg_ok else '✗ not found — video conversion disabled'}",
        f"unrar     : {'✓ available' if unrar_ok  else '✗ not found — RAR support limited'}",
        "",
        f"Python    : {platform.python_version()}",
        f"Started   : {started_at}",
    ]
    log.info("\n%s", _box(banner_lines))
    log.info("Bot is ready. Polling started.")

    if ADMIN_ID:
        ok = lambda v: "✅" if v else "⚠️"
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🟢 <b>Бот запущен</b>\n\n"
                f"👤 @{me.username}\n"
                f"{'🏠' if local_api else '🌐'} API: {'локальный' if local_api else 'публичный'}\n"
                f"📦 Лимит файла: <b>{human_size(MAX_FILE_SIZE)}</b>\n"
                f"{ok(ffmpeg_ok)} ffmpeg: {'доступен' if ffmpeg_ok else 'НЕ НАЙДЕН'}\n"
                f"{ok(unrar_ok)} unrar:  {'доступен' if unrar_ok  else 'НЕ НАЙДЕН'}\n\n"
                f"🕐 {started_at}",
            )
        except Exception as exc:
            log.warning("Could not notify admin (%s): %s", ADMIN_ID, exc)


async def _on_shutdown(bot: Bot) -> None:
    log.info("Shutting down...")
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, "🔴 <b>Бот остановлен</b>")
        except Exception:
            pass


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set. Create a .env file.")

    from handlers import start, image_handler, video_handler, document_router

    bot = _make_bot()
    dp  = Dispatcher()

    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)

    dp.include_router(start.router)
    dp.include_router(image_handler.router)
    dp.include_router(video_handler.router)
    dp.include_router(document_router.router)

    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
