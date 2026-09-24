"""Inline-клавиатуры."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CALLBACKS = {
    "menu_learn": "menu:learn",
    "menu_quiz": "menu:quiz",
    "menu_progress": "menu:progress",
    "menu_list": "menu:list",
    "learn_reveal": "learn:reveal",
    "learn_know": "learn:know",
    "learn_repeat": "learn:repeat",
    "learn_all": "learn:all",
    "quiz_mode_img": "quiz:mode:img",
    "quiz_mode_def": "quiz:mode:def",
    "quiz_mode_con": "quiz:mode:con",
    "quiz_next_img": "quiz:next:img",
    "quiz_next_def": "quiz:next:def",
    "quiz_next_con": "quiz:next:con",
}


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Карточки (повторение)", callback_data=CALLBACKS["menu_learn"])],
        [InlineKeyboardButton(text="🎯 Викторина", callback_data=CALLBACKS["menu_quiz"])],
        [InlineKeyboardButton(text="📊 Мой прогресс", callback_data=CALLBACKS["menu_progress"])],
        [InlineKeyboardButton(text="📋 Все термины", callback_data=CALLBACKS["menu_list"])],
    ])


def reveal_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Показать ответ", callback_data=CALLBACKS["learn_reveal"])],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])


def answer_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Запомнил", callback_data=CALLBACKS["learn_know"]),
            InlineKeyboardButton(text="🔄 Повторить", callback_data=CALLBACKS["learn_repeat"]),
        ],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])


def done_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить все", callback_data=CALLBACKS["learn_all"])],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])


def quiz_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Угадай по определению", callback_data=CALLBACKS["quiz_mode_def"])],
        [InlineKeyboardButton(text="⚔️ Контраст (пары глаголов)", callback_data=CALLBACKS["quiz_mode_con"])],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])


def quiz_answer_buttons(mode: str, options: list[dict], correct: dict) -> InlineKeyboardMarkup:
    """Варианты ответа; callback кодирует id выбранного и правильного термина.

    Используются числовые id, а не названия: кириллические названия в
    callback_data превышают лимит Telegram в 64 байта.
    """
    rows = []
    for opt in options:
        cb = f"quiz:ans:{mode}:{opt['id']}:{correct['id']}"
        rows.append([InlineKeyboardButton(text=opt["verb"], callback_data=cb)])
    rows.append([InlineKeyboardButton(text="⏭ Пропустить",
                                      callback_data=f"quiz:skip:{mode}:{correct['id']}")])
    rows.append([InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quiz_next_button(mode: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Дальше", callback_data=f"quiz:next:{mode}")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])


def results_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 Показать результат", callback_data="quiz:finish")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])


def home_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="menu:start")],
    ])