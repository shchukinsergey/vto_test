"""Тесты алгоритма повторения Leitner."""

import time

from bot import srs


def test_promote_increments_box():
    box, nxt = srs.promote(0)
    assert box == 1
    assert nxt > time.time()


def test_promote_caps_at_learned_box():
    box, nxt = srs.promote(srs.LEARNED_BOX)
    assert box == srs.LEARNED_BOX
    assert nxt > time.time()


def test_reset_returns_to_box_zero():
    box, nxt = srs.reset(3)
    assert box == 0
    assert nxt <= time.time() + 1  # повтор сейчас


def test_intervals_increase():
    now = 1_000_000.0
    _, n1 = srs.promote(0, now)
    _, n3 = srs.promote(2, now)
    _, n4 = srs.promote(3, now)
    assert n3 > n1
    assert n4 > n3


def test_is_due():
    entry = {"next_review": time.time() - 1}
    assert srs.is_due(entry)


def test_not_due_in_future():
    entry = {"next_review": time.time() + 10_000}
    assert not srs.is_due(entry)


def test_is_learned_only_at_top_box():
    assert not srs.is_learned(3)
    assert srs.is_learned(4)