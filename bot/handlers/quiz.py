"""Викторина: серия из 5 вопросов по определению / контрастная пара."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from .. import db, quiz as qz, srs
from ..content import CATEGORY_LABELS
from ..keyboards import (main_menu, quiz_answer_buttons, quiz_menu,
                         quiz_next_button, results_button)
from .helpers import answer_callback

router = Router()

QUIZ_TOTAL = 5


class QuizState(StatesGroup):
    session = State()


async def send_question(bot, chat_id: int, mode: str,
                        current: int | None = None,
                        total: int | None = None) -> None:
    """Отправляет вопрос викторины. current/total — для прогресса «Вопрос X/Y».

    Без current/total (например, из планировщика) шлёт одиночный вопрос.
    """
    terms = await db.all_terms()
    correct = qz.pick_question(terms)

    if mode == "con":
        options = qz.build_contrast_question(terms, correct)
        body = (
            f"⚔️ <b>Контрастная пара</b>\n\n"
            f"<b>Что означает:</b>\n{correct['definition']}\n\n"
            f"Различи похожие термины и выбери правильный:"
        )
    else:  # def
        options = qz.build_options(terms, correct, 4)
        body = (f"<b>Что означает:</b>\n{correct['definition']}\n\n"
                f"<i>Категория:</i> {CATEGORY_LABELS.get(correct['category'], correct['category'])}")

    if current is not None and total is not None:
        header = f"❓ Вопрос {current}/{total}\n\n"
    else:
        header = ""
    text = header + body

    markup = quiz_answer_buttons(mode, options, correct)
    await bot.send_message(chat_id, text, reply_markup=markup)


@router.callback_query(F.data == "menu:quiz")
async def cb_quiz_menu(callback: CallbackQuery) -> None:
    await answer_callback(callback, "Выбери режим викторины:", quiz_menu())


@router.callback_query(F.data.in_({"quiz:mode:def", "quiz:mode:con"}))
async def cb_quiz_start(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":")[2]
    await state.set_state(QuizState.session)
    await state.set_data({"mode": mode, "total": QUIZ_TOTAL,
                          "current": 1, "correct": 0})
    await send_question(callback.bot, callback.message.chat.id, mode, 1, QUIZ_TOTAL)


def _parse_answer(data: str) -> tuple[str, int, int] | None:
    """Разбирает quiz:ans:<mode>:<chosen_id>:<correct_id>."""
    parts = data.split(":")
    if len(parts) != 5:
        return None
    return parts[2], int(parts[3]), int(parts[4])


async def _advance(callback: CallbackQuery, state: FSMContext,
                   feedback: str, correct_now: bool) -> None:
    """Показывает фидбек и двигает сессию; на последнем вопросе — к результату."""
    data = await state.get_data()
    if not data.get("mode"):
        # Устаревшая/пустая сессия — просто фидбек и меню.
        await callback.message.answer(feedback, reply_markup=main_menu())
        return
    if correct_now:
        data["correct"] += 1
    data["current"] += 1
    finished = data["current"] > data["total"]
    await state.set_data(data)
    markup = results_button() if finished else quiz_next_button(data["mode"])
    await callback.message.answer(feedback, reply_markup=markup)


async def _summary(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    total = data.get("total", QUIZ_TOTAL)
    correct = data.get("correct", 0)
    await state.clear()
    msg = f"🎯 <b>Результат:</b> верно <b>{correct} из {total}</b>."
    await callback.message.answer(msg, reply_markup=main_menu())


@router.callback_query(F.data.startswith("quiz:ans:"))
async def cb_quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    parsed = _parse_answer(callback.data)
    if parsed is None:
        await callback.message.answer("Что-то пошло не так. Начни заново:",
                                      reply_markup=main_menu())
        return
    mode, chosen_id, correct_id = parsed
    terms = await db.all_terms()
    by_id = {t["id"]: t for t in terms}
    correct = by_id.get(correct_id)
    chosen = by_id.get(chosen_id)
    ok = chosen_id == correct_id

    await db.record_activity(callback.from_user.id)
    if correct:
        progress = (await db.get_progress(callback.from_user.id)).get(correct["id"], {})
        box = progress.get("box", 0)
        new_box, nxt = srs.promote(box) if ok else srs.reset(box)
        await db.record_review(callback.from_user.id, correct["id"], new_box, nxt, ok)

    head = "✅ Верно!" if ok else f"❌ Это «{chosen['verb']}»."
    text = (
        f"{head}\n\n"
        f"<b>{correct['verb']}</b> — {correct['definition']}\n"
        f"<i>Пример:</i> {correct['example']}"
        if correct else head
    )
    await _advance(callback, state, text, ok)


@router.callback_query(F.data.startswith("quiz:skip:"))
async def cb_quiz_skip(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    # quiz:skip:<mode>:<correct_id>
    mode, correct_id = parts[2], parts[3]
    terms = await db.all_terms()
    by_id = {t["id"]: t for t in terms}
    correct = by_id.get(int(correct_id))
    text = (f"Правильный ответ: <b>{correct['verb']}</b>\n\n{correct['definition']}"
            if correct else "Пропущено.")
    await _advance(callback, state, text, False)


@router.callback_query(F.data.startswith("quiz:next:"))
async def cb_quiz_next(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    mode = data.get("mode") or callback.data.split(":")[2]
    if not data.get("mode") or data.get("current", 0) > data.get("total", 0):
        await _summary(callback, state)
        return
    await send_question(callback.bot, callback.message.chat.id,
                        mode, data["current"], data["total"])


@router.callback_query(F.data == "quiz:finish")
async def cb_quiz_finish(callback: CallbackQuery, state: FSMContext) -> None:
    await _summary(callback, state)