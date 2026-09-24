"""Точка входа бота ВТО.

Запуск:
    python -m bot
"""
import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from . import config, db
from .bot import build_dispatcher
from .scheduler import reminder_loop


async def main() -> None:
    token = config.require_token()
    await db.init_db()

    bot = Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()

    # Планировщик напоминаний.
    reminder_task = asyncio.create_task(reminder_loop(bot))

    try:
        print("Бот запущен. Для остановки — Ctrl+C.")
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())