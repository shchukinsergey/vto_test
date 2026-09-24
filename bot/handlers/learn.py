"""Карточки с интервальным повторением (SRS/Leitner)."""

import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from .. import db, srs
from ..content import CATEGORY_LABELS
from ..keyboards import answer_buttons, done_buttons, main_menu, reveal_button
from .helpers import answer_callback, send_card

router = Router()


class LearnState(StatesGroup):
    session = State()


def _term_map(terms: list[dict]) -> dict[int, dict]:
    return {t["id"]: t for t in terms}


async def _session_term(data: dict) -> dict | None:
    """Термин текущей карточки сессии; None, если сессия устарела/пуста."""
    ids = data.get("ids")
    if not ids:
        return None
    idx = data.get("idx", 0)
    if idx < 0 or idx >= len(ids):
        return None
    return _term_map(await db.all_terms()).get(ids[idx])


async def _due_terms(user_id: int) -> list[dict]:
    terms = await db.all_terms()
    progress = await db.get_progress(user_id)
    due = []
    for t in terms:
        entry = progress.get(t["id"])
        if entry is None or srs.is_due(entry):
            due.append(t)
    return due


async def _start_session(callback: CallbackQuery, state: FSMContext,
                         terms: list[dict], all_mode: bool) -> None:
    ids = [t["id"] for t in terms]
    await state.set_state(LearnState.session)
    await state.set_data({"all": all_mode, "ids": ids, "idx": 0})
    await _send_question(callback.message, state)


async def _send_question(message, state: FSMContext) -> None:
    data = await state.get_data()
    ids = data["ids"]
    idx = data["idx"]
    if idx >= len(ids):
        await state.clear()
        await message.answer(
            "🎉 Ты повторил все карточки из этой подборки!",
            reply_markup=done_buttons(),
        )
        return
    terms = _term_map(await db.all_terms())
    term = terms[ids[idx]]
    text = (f"<b>Термин:</b> {term['verb']}\n"
            f"<i>Категория:</i> {CATEGORY_LABELS.get(term['category'], term['category'])}")
    await message.answer(text, reply_markup=reveal_button())


async def _send_answer(message, state: FSMContext) -> None:
    data = await state.get_data()
    term = await _session_term(data)
    if term is None:
        await state.clear()
        await message.answer(
            "⏳ Сессия повторения завершилась. Начни заново из меню.",
            reply_markup=main_menu(),
        )
        return
    caption = (
        f"<b>{term['verb']}</b>\n\n{term['definition']}\n\n"
        f"<i>Пример:</i> {term['example']}"
    )
    await send_card(message.bot, message.chat.id, caption, answer_buttons())


@router.callback_query(F.data == "menu:learn")
async def cb_learn(callback: CallbackQuery, state: FSMContext) -> None:
    due = await _due_terms(callback.from_user.id)
    if not due:
        await answer_callback(
            callback,
            "🌤 На сегодня все карточки повторены! Загляни завтра.\n\n"
            "Или потренируйся на всём наборе прямо сейчас:",
            done_buttons(),
        )
        return
    await _start_session(callback, state, due, all_mode=False)


@router.callback_query(F.data == "learn:all")
async def cb_learn_all(callback: CallbackQuery, state: FSMContext) -> None:
    terms = await db.all_terms()
    await _start_session(callback, state, terms, all_mode=True)


@router.callback_query(F.data == "learn:reveal")
async def cb_reveal(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_answer(callback.message, state)


async def _record_and_next(callback: CallbackQuery, state: FSMContext,
                           correct: bool) -> None:
    data = await state.get_data()
    term = await _session_term(data)
    if term is None:
        await state.clear()
        await callback.message.answer(
            "⏳ Сессия повторения завершилась. Начни заново из меню.",
            reply_markup=main_menu(),
        )
        return
    progress = (await db.get_progress(callback.from_user.id)).get(term["id"], {})
    box = progress.get("box", 0)
    if correct:
        new_box, nxt = srs.promote(box)
    else:
        new_box, nxt = srs.reset(box)
    await db.record_review(callback.from_user.id, term["id"], new_box, nxt, correct)
    await db.record_activity(callback.from_user.id)
    data["idx"] += 1
    await state.set_data(data)
    await _send_question(callback.message, state)


@router.callback_query(F.data == "learn:know")
async def cb_know(callback: CallbackQuery, state: FSMContext) -> None:
    await _record_and_next(callback, state, correct=True)


@router.callback_query(F.data == "learn:repeat")
async def cb_repeat(callback: CallbackQuery, state: FSMContext) -> None:
    await _record_and_next(callback, state, correct=False)