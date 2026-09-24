"""Общие вспомогательные функции для хендлеров."""

from aiogram.types import (CallbackQuery, InlineKeyboardMarkup, Message)

from .. import db
from ..content import CATEGORY_LABELS
from ..keyboards import main_menu


async def ensure_user(message: Message) -> None:
    """Первичная инициализация пользователя (stats + активность)."""
    await db.record_activity(message.from_user.id)


async def send_or_edit(message: Message, text: str, reply_markup: InlineKeyboardMarkup,
                       *, edit: bool = False) -> None:
    if edit:
        await message.edit_text(text, reply_markup=reply_markup)
    else:
        await message.answer(text, reply_markup=reply_markup)


async def answer_callback(callback: CallbackQuery, text: str,
                          reply_markup: InlineKeyboardMarkup) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


def term_line(t: dict) -> str:
    return (
        f"<b>{t['verb']}</b> — {t['definition']}\n"
        f"<i>Пример:</i> {t['example']}\n"
        f"<i>Категория:</i> {CATEGORY_LABELS.get(t['category'], t['category'])}"
    )


def list_text(terms: list[dict]) -> str:
    by_cat: dict[str, list[str]] = {}
    for t in terms:
        by_cat.setdefault(t["category"], []).append(f"• <b>{t['verb']}</b>")
    lines = ["<b>Швейные термины</b>\n"]
    for cat in ("общее", "швы", "посадка", "соединение", "строчки", "стежка",
                "ручные", "конструкция", "пар"):
        if cat in by_cat:
            lines.append(f"\n<b>{CATEGORY_LABELS[cat]}:</b>")
            lines.extend(by_cat[cat])
    return "\n".join(lines)


async def send_card(bot, chat_id: int, caption: str,
                    reply_markup: InlineKeyboardMarkup) -> None:
    """Отправляет карточку текстом (без картинок)."""
    await bot.send_message(chat_id, caption, reply_markup=reply_markup)