"""Алгоритм повторения Leitner для карточек.

5 коробок с растущими интервалами. «Запомнил» переводит карточку на коробку
выше и планирует следующее повторение через интервал этой коробки. «Повторить»
сбрасывает карточку в коробку 0 (повтор сейчас). Карточка считается выученной,
когда достигает последней коробки (4).
"""

import time

NUM_BOXES = 5
# Интервалы (в днях) для каждой коробки после успешного ответа.
INTERVALS_DAYS = [0, 1, 3, 7, 14]
LEARNED_BOX = NUM_BOXES - 1  # 4

DAY = 24 * 3600


def next_review(box: int, now: float | None = None) -> float:
    """Timestamp следующего повторения после успеха на текущей коробке `box`.

    box — коробка ДО повышения. Возвращаемое время соответствует новой коробке.
    """
    if now is None:
        now = time.time()
    new_box = min(box + 1, LEARNED_BOX)
    return now + INTERVALS_DAYS[new_box] * DAY


def promote(box: int, now: float | None = None) -> tuple[int, float]:
    """Успешный ответ: возвращает (новая коробка, время следующего повтора)."""
    new_box = min(box + 1, LEARNED_BOX)
    return new_box, next_review(box, now)


def reset(box: int, now: float | None = None) -> tuple[int, float]:
    """Неуспешный ответ: сброс в коробку 0, повтор сейчас."""
    if now is None:
        now = time.time()
    return 0, now


def is_due(entry: dict, now: float | None = None) -> bool:
    """Карточка подлежит повторению, если её next_review <= сейчас."""
    if now is None:
        now = time.time()
    return entry.get("next_review", 0) <= now


def is_learned(box: int) -> bool:
    return box >= LEARNED_BOX