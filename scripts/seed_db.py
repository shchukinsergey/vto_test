#!/usr/bin/env python3
"""Инициализация/обновление БД (схема + термины).

Добавляет недостающие термины из bot/content.py в существующую базу.

Запуск:
    python scripts/seed_db.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import db  # noqa: E402


async def main() -> None:
    await db.init_db()
    print("БД инициализирована:", db.DB_PATH)
    print("Терминов в базе:", len(await db.all_terms()))


if __name__ == "__main__":
    asyncio.run(main())