from __future__ import annotations

import asyncio
import os
import platform
import shutil
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_ID
from utils.logger import setup_logging
from utils.stats import stats
from utils.file_utils import cleanup_temp_dir
from utils.video_utils import ffmpeg_available

log = setup_logging()


def _box(lines: list[str], width: int = 58) -> str:
    bar = "─" * width
    rows = "\n".join(f"│  {ln:<{width - 4}}│" for ln in lines)
    return f"┌{bar}┐\n{rows}\n└{bar}┘"


async def _on_startup(bot: Bot) -> None:
    removed = cleanup_temp_dir()
    if removed:
        log.info("Cleaned up %d leftover temp file(s) from previous session", removed)

    await stats.on_startup()

    me = await bot.get_me()
    ffmpeg_ok  = ffmpeg_available()
    unrar_ok   = bool(shutil.which("unrar") or shutil.which("unrar-free"))
    python_ver = platform.python_version()
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    banner_lines = [
        f"Bot     : @{me.username}  (ID {me.id})",
        f"Name    : {me.full_name}",
        "",
        f"ffmpeg  : {'✓ available' if ffmpeg_ok  else '✗ not found  — video conversion disabled'}",
        f"unrar   : {'✓ available' if unrar_ok   else '✗ not found  — RAR support limited'}",
        "",
        f"Python  : {python_ver}",
        f"Started : {started_at}",
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
                f"{ok(ffmpeg_ok)} ffmpeg: {'доступен' if ffmpeg_ok else 'НЕ НАЙДЕН — конвертация видео выключена'}\n"
                f"{ok(unrar_ok)} unrar: {'доступен' if unrar_ok else 'НЕ НАЙДЕН — RAR работает ограниченно'}\n\n"
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

    # Import routers here to keep startup log above their module-level code
    from handlers import start, image_handler, video_handler, document_router

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.startup.register(_on_startup)
    dp.shutdown.register(_on_shutdown)

    # Router order matters: callbacks first, then typed message handlers,
    # then the catch-all document router.
    dp.include_router(start.router)
    dp.include_router(image_handler.router)   # F.photo  + img:* callbacks
    dp.include_router(video_handler.router)   # F.video  + vid:* callbacks
    dp.include_router(document_router.router) # F.document → dispatch by ext

    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
