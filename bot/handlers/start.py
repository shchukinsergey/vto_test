"""Обработка старта, меню и списка терминов."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from .. import db
from ..keyboards import main_menu
from .helpers import answer_callback, ensure_user, list_text, send_or_edit

router = Router()

WELCOME = (
    "👋 Привет! Я помогу выучить швейную терминологию: влажно-тепловую "
    "обработку (ВТО), машинные и ручные операции, детали кроя.\n\n"
    "Вот что умею:\n"
    "📖 <b>Карточки</b> — повторение с интервалами (как в Anki)\n"
    "🎯 <b>Викторина</b> — угадай термин по определению или различи "
    "контрастную пару\n"
    "📊 <b>Прогресс</b> — сколько выучил и серия дней\n\n"
    "Выбирай в меню 👇"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await ensure_user(message)
    await send_or_edit(message, WELCOME, main_menu())


@router.callback_query(F.data == "menu:start")
async def cb_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await answer_callback(callback, WELCOME, main_menu())


@router.callback_query(F.data == "menu:list")
async def cb_list(callback: CallbackQuery) -> None:
    terms = await db.all_terms()
    await answer_callback(callback, list_text(terms), main_menu())