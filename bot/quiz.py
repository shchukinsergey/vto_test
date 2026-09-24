"""Чистая логика викторины: выбор вопроса и вариантов ответа.

Функции не зависят от aiogram и покрываются юнит-тестами.
"""

import random


def pick_distractors(terms: list[dict], correct: dict, count: int = 3) -> list[dict]:
    """Выбирает дистракторы: в первую очередь из той же категории.

    `terms` — список всех терминов, `correct` — правильный термин.
    Возвращает список из `count` терминов-дистракторов.
    """
    pool = [t for t in terms if t["id"] != correct["id"]]
    same_cat = [t for t in pool if t["category"] == correct["category"]]
    random.shuffle(pool)
    random.shuffle(same_cat)
    chosen = same_cat[:count]
    for t in pool:
        if len(chosen) >= count:
            break
        if t not in chosen:
            chosen.append(t)
    return chosen


def build_options(terms: list[dict], correct: dict, count: int = 4) -> list[dict]:
    """Собирает варианты ответа: правильный + дистракторы, перемешанные."""
    distractors = pick_distractors(terms, correct, count - 1)
    options = distractors + [correct]
    random.shuffle(options)
    return options


def pick_question(terms: list[dict], exclude_ids: set[int] | None = None) -> dict:
    """Выбирает случайный термин для вопроса."""
    pool = [t for t in terms if not (exclude_ids and t["id"] in exclude_ids)]
    if not pool:
        pool = terms
    return random.choice(pool)


def build_contrast_question(terms: list[dict], correct: dict) -> list[dict]:
    """Для контрастного режима: варианты обязательно включают контрастную пару.

    Гарантирует, что партнёр по contrast_group есть среди вариантов, чтобы
    проверить различение похожих глаголов.
    """
    group = [t for t in terms if t["contrast_group"] == correct["contrast_group"]]
    options = [t for t in group if t["id"] != correct["id"]]  # партнёры по паре
    others = pick_distractors(terms, correct, 4 - len(options) - 1)
    options += others + [correct]
    random.shuffle(options)
    return options