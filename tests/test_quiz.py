"""Тесты логики викторины: дистракторы и контраст."""

from bot import keyboards, quiz


def _terms():
    # категории: швы (4), посадка (4), общее (2)
    data = [
        ("заутюжить", "швы", "g1"),
        ("разутьюжить", "швы", "g1"),
        ("приутюжить", "швы", None),
        ("отутюжить", "швы", None),
        ("сутюжить", "посадка", "g2"),
        ("оттянуть", "посадка", "g2"),
        ("припосадить", "посадка", None),
        ("увлажнить", "посадка", None),
        ("отпарить", "общее", None),
        ("декатировать", "общее", None),
    ]
    return [{"id": i, "verb": v, "category": c, "contrast_group": g}
            for i, (v, c, g) in enumerate(data)]


def test_distractors_exclude_correct_and_are_unique():
    terms = _terms()
    correct = terms[0]
    d = quiz.pick_distractors(terms, correct, 3)
    assert len(d) == 3
    assert correct not in d
    assert len({t["id"] for t in d}) == 3


def test_distractors_prefer_same_category():
    terms = _terms()
    correct = terms[0]  # категория "швы"
    d = quiz.pick_distractors(terms, correct, 3)
    assert all(t["category"] == "швы" for t in d), "должны браться из той же категории"


def test_build_options_contains_correct_once():
    terms = _terms()
    correct = terms[0]
    opts = quiz.build_options(terms, correct, 4)
    assert len(opts) == 4
    assert sum(1 for o in opts if o["id"] == correct["id"]) == 1


def test_contrast_question_includes_partner():
    terms = _terms()
    correct = terms[0]  # заутюжить, группа g1, партнёр разутьюжить
    opts = quiz.build_contrast_question(terms, correct)
    partner = [t for t in terms if t["contrast_group"] == "g1" and t["id"] != correct["id"]][0]
    assert partner in opts, "контрастная пара должна быть среди вариантов"
    assert correct in opts


def test_callback_data_stays_within_telegram_limit():
    """Кириллические названия не должны ломать callback_data (лимит 64 байта)."""
    from bot import content

    terms = [{"id": i, "verb": t["verb"]} for i, t in enumerate(content.TERMS)]
    for correct in terms:
        others = [t for t in terms if t["id"] != correct["id"]][:3]
        options = others + [correct]
        markup = keyboards.quiz_answer_buttons("def", options, correct)
        for row in markup.inline_keyboard:
            for btn in row:
                data = btn.callback_data
                if data and data.startswith("quiz:ans:"):
                    assert len(data.encode("utf-8")) <= 64, (
                        f"callback_data слишком длинный: {data!r}"
                    )