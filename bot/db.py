"""Работа с SQLite через aiosqlite: схема БД и асинхронные хелперы."""

import time
from pathlib import Path

import aiosqlite

from .content import TERMS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "vto.db"
IMAGES_DIR = DATA_DIR / "images"

SCHEMA = """
CREATE TABLE IF NOT EXISTS terms (
    id          INTEGER PRIMARY KEY,
    verb        TEXT NOT NULL UNIQUE,
    definition  TEXT NOT NULL,
    example     TEXT NOT NULL,
    category    TEXT NOT NULL,
    contrast_group TEXT
);

CREATE TABLE IF NOT EXISTS progress (
    user_id      INTEGER NOT NULL,
    term_id      INTEGER NOT NULL,
    box          INTEGER NOT NULL DEFAULT 0,
    next_review  REAL NOT NULL DEFAULT 0,
    correct      INTEGER NOT NULL DEFAULT 0,
    wrong        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, term_id)
);

CREATE TABLE IF NOT EXISTS user_stats (
    user_id      INTEGER PRIMARY KEY,
    streak       INTEGER NOT NULL DEFAULT 0,
    last_active  REAL NOT NULL DEFAULT 0,
    level        INTEGER NOT NULL DEFAULT 1,
    total_reviews INTEGER NOT NULL DEFAULT 0
);
"""


async def connect() -> aiosqlite.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return await aiosqlite.connect(DB_PATH)


async def init_db() -> None:
    conn = await connect()
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.executescript(SCHEMA)
    # Добавляем термины из контента, которых ещё нет (INSERT OR IGNORE).
    await conn.executemany(
        "INSERT OR IGNORE INTO terms "
        "(verb, definition, example, category, contrast_group) VALUES (?, ?, ?, ?, ?)",
        [(t["verb"], t["definition"], t["example"], t["category"],
          t["contrast_group"]) for t in TERMS],
    )
    await conn.commit()
    await conn.close()


# ---------- Прогресс по терминам ----------

async def get_progress(user_id: int) -> dict[int, dict]:
    """Возвращает {term_id: {...}} прогресс пользователя по всем терминам."""
    conn = await connect()
    rows = await conn.execute_fetchall(
        "SELECT term_id, box, next_review, correct, wrong FROM progress WHERE user_id=?",
        (user_id,),
    )
    await conn.close()
    return {r[0]: {"box": r[1], "next_review": r[2], "correct": r[3], "wrong": r[4]} for r in rows}


async def all_terms() -> list[dict]:
    conn = await connect()
    rows = await conn.execute_fetchall(
        "SELECT id, verb, definition, example, category, contrast_group FROM terms"
    )
    await conn.close()
    return [
        {"id": r[0], "verb": r[1], "definition": r[2], "example": r[3],
         "category": r[4], "contrast_group": r[5]}
        for r in rows
    ]


async def term_by_verb(verb: str) -> dict | None:
    conn = await connect()
    rows = await conn.execute_fetchall(
        "SELECT id, verb, definition, example, category, contrast_group FROM terms WHERE verb=?",
        (verb,),
    )
    await conn.close()
    if not rows:
        return None
    r = rows[0]
    return {"id": r[0], "verb": r[1], "definition": r[2], "example": r[3],
            "category": r[4], "contrast_group": r[5]}


async def record_review(user_id: int, term_id: int, box: int, next_review: float,
                        correct: bool) -> None:
    """Записывает ответ по карточке и обновляет прогресс."""
    conn = await connect()
    # upsert
    await conn.execute(
        "INSERT INTO progress (user_id, term_id, box, next_review, correct, wrong) "
        "VALUES (?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(user_id, term_id) DO UPDATE SET "
        "box=excluded.box, next_review=excluded.next_review, "
        "correct=progress.correct + excluded.correct, wrong=progress.wrong + excluded.wrong",
        (user_id, term_id, box, next_review, 1 if correct else 0, 0 if correct else 1),
    )
    await conn.commit()
    await conn.close()


async def record_activity(user_id: int) -> None:
    """Обновляет серию дней подряд и счётчик повторов."""
    conn = await connect()
    now = time.time()
    day = 24 * 3600
    rows = await conn.execute_fetchall(
        "SELECT streak, last_active, total_reviews FROM user_stats WHERE user_id=?",
        (user_id,),
    )
    if not rows:
        await conn.execute(
            "INSERT INTO user_stats (user_id, streak, last_active, total_reviews) "
            "VALUES (?, 1, ?, 1)",
            (user_id, now),
        )
    else:
        streak, last, total = rows[0]
        if now - last > day:  # пропущен день — серия сбрасывается
            streak = 1
        elif now - last >= 0 and (int(now) // 86400) != (int(last) // 86400):
            streak += 1
        await conn.execute(
            "UPDATE user_stats SET streak=?, last_active=?, total_reviews=? WHERE user_id=?",
            (streak, now, total + 1, user_id),
        )
    await conn.commit()
    await conn.close()


async def get_stats(user_id: int) -> dict:
    conn = await connect()
    rows = await conn.execute_fetchall(
        "SELECT streak, level, total_reviews FROM user_stats WHERE user_id=?",
        (user_id,),
    )
    await conn.close()
    if not rows:
        return {"streak": 0, "level": 1, "total_reviews": 0}
    return {"streak": rows[0][0], "level": rows[0][1], "total_reviews": rows[0][2]}


async def all_user_ids() -> list[int]:
    conn = await connect()
    rows = await conn.execute_fetchall("SELECT user_id FROM user_stats")
    await conn.close()
    return [r[0] for r in rows]