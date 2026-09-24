"""Прогресс пользователя."""

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from .. import db, srs
from ..keyboards import home_button
from .helpers import answer_callback

router = Router()


@router.callback_query(F.data == "menu:progress")
async def cb_progress(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    terms = await db.all_terms()
    progress = await db.get_progress(user_id)
    stats = await db.get_stats(user_id)

    learned = 0
    in_progress = 0
    new = 0
    due_today = 0
    for t in terms:
        entry = progress.get(t["id"], {})
        box = entry.get("box", 0)
        if srs.is_learned(box):
            learned += 1
        elif box >= 1:
            in_progress += 1
        else:
            new += 1
        if srs.is_due(entry):
            due_today += 1

    total = len(terms)
    pct = round(100 * learned / total) if total else 0

    last = stats.get("last_active", 0) or 0
    last_dt = datetime.fromtimestamp(last).strftime("%d.%m %H:%M") if last else "—"

    text = (
        f"📊 <b>Твой прогресс</b>\n\n"
        f"🎯 Выучено: <b>{learned} / {total}</b> ({pct}%)\n"
        f"📚 В процессе изучения: <b>{in_progress}</b>\n"
        f"🆕 Ещё не начато: <b>{new}</b>\n"
        f"🔁 К повторению сегодня: <b>{due_today}</b>\n\n"
        f"🔥 Серия дней: <b>{stats['streak']}</b>\n"
        f"🔄 Всего ответов: <b>{stats['total_reviews']}</b>\n"
        f"Активность: {last_dt}\n\n"
        f"<i>Слово считается выученным после 4 верных ответов подряд. "
        f"«В процессе» — ты уже закрепил его в памяти, но повторяешь по "
        f"растущим интервалам.</i>"
    )
    await answer_callback(callback, text, home_button())