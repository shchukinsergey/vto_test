"""Настройки: токен и время напоминаний из переменных окружения / .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# Время ежедневных напоминаний (HH:MM).
_reminder = os.getenv("REMINDER_TIMES", "12:00,19:00")
REMINDER_TIMES: list[tuple[int, int]] = []
for part in _reminder.split(","):
    hh, mm = part.strip().split(":")
    REMINDER_TIMES.append((int(hh), int(mm)))


def require_token() -> str:
    if not BOT_TOKEN:
        raise SystemExit(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env и вставьте токен "
            "из @BotFather."
        )
    return BOT_TOKEN