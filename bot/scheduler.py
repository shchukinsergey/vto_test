"""Планировщик ежедневных напоминаний.

Раз в заданные времена (REMINDER_TIMES) присылает всем активным пользователям
один вопрос викторины. Работает, пока процесс бота запущен.
"""

import asyncio
import random
from datetime import datetime

from . import config, db
from .handlers.quiz import send_question

_MODES = ["def", "con"]
_LAST_SENT: dict[tuple[int, str], str] = {}  # (user_id, "HH:MM") -> date


async def reminder_loop(bot) -> None:
    while True:
        now = datetime.now()
        key = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")
        if key in config.REMINDER_TIMES:
            for user_id in await db.all_user_ids():
                last = _LAST_SENT.get((user_id, key))
                if last == today:
                    continue
                _LAST_SENT[(user_id, key)] = today
                mode = random.choice(_MODES)
                try:
                    await send_question(bot, user_id, mode)
                except Exception as exc:  # не роняем цикл из-за одной отправки
                    print(f"[scheduler] не удалось отправить {user_id}: {exc}")
        await asyncio.sleep(30)