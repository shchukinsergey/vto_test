"""Генерация простых PNG-схем для глаголов ВТО (Pillow).

Схемы — минималистичные: ткань, шов, стрелки направления, пар. Они нужны,
чтобы наглядно различить контрастные пары (заутюжить/разутьюжить,
сутюжить/оттянуть).
"""

from pathlib import Path

from PIL import Image, ImageDraw

from .db import IMAGES_DIR

W, H = 500, 360
BG = (255, 255, 255)
FABRIC = (224, 224, 224)
FABRIC_EDGE = (160, 160, 160)
INK = (40, 40, 40)
ARROW = (200, 60, 60)
STEAM = (140, 190, 230)


def _new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def _arrow(d: ImageDraw.ImageDraw, x1, y1, x2, y2, color=ARROW, width=8):
    d.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # наконечник
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 24
    for da in (math.pi - 0.5, math.pi + 0.5):
        dx = L * math.cos(ang + da)
        dy = L * math.sin(ang + da)
        d.line([(x2, y2), (x2 + dx, y2 + dy)], fill=color, width=width)


def _iron(d: ImageDraw.ImageDraw, cx, cy, scale=1.0):
    """Стилизованный утюг: подошва + корпус + ручка."""
    s = scale
    d.rounded_rectangle(
        [(cx - 70 * s, cy - 20 * s), (cx + 70 * s, cy + 20 * s)],
        radius=18 * s, fill=(70, 70, 70),
    )
    d.rounded_rectangle(
        [(cx - 55 * s, cy - 70 * s), (cx + 30 * s, cy - 20 * s)],
        radius=14 * s, fill=(90, 90, 90),
    )
    # ручка
    d.rounded_rectangle(
        [(cx - 30 * s, cy - 95 * s), (cx + 45 * s, cy - 70 * s)],
        radius=10 * s, fill=(150, 110, 60),
    )


def _fabric_block(d: ImageDraw.ImageDraw, x, y, w, h, label=None):
    d.rectangle([(x, y), (x + w, y + h)], fill=FABRIC, outline=FABRIC_EDGE, width=3)


# ---------- Типы схем ----------

def flat(img, d, verb):
    """Утюжка: ткань + утюг + стрелки давления вниз (выравнивание)."""
    _fabric_block(d, 120, 170, 260, 60)
    _iron(d, 250, 120)
    _arrow(d, 210, 60, 210, 100)  # давление
    _arrow(d, 290, 60, 290, 100)
    d.text((150, 20), "выравнивание ткани", fill=INK, font=_font(18))


def seam(img, d, verb):
    """Припуски шва. verb в {заутюжить, разутьюжить}."""
    # два слоя ткани
    _fabric_block(d, 120, 120, 260, 45)
    _fabric_block(d, 120, 165, 260, 45)
    # линия шва
    d.line([(250, 120), (250, 210)], fill=INK, width=4)
    if verb == "заутюжить":
        # припуски в одну сторону (вправо)
        d.rectangle([(360, 120), (440, 165)], fill=FABRIC, outline=FABRIC_EDGE, width=3)
        _arrow(d, 300, 142, 360, 142)
        d.text((150, 20), "припуски — в одну сторону", fill=INK, font=_font(18))
    else:  # разутьюжить
        d.rectangle([(60, 165), (120, 210)], fill=FABRIC, outline=FABRIC_EDGE, width=3)
        d.rectangle([(380, 165), (440, 210)], fill=FABRIC, outline=FABRIC_EDGE, width=3)
        _arrow(d, 120, 187, 70, 187)
        _arrow(d, 380, 187, 430, 187)
        d.text((120, 20), "припуски — в две стороны", fill=INK, font=_font(18))
    _iron(d, 250, 250, scale=0.9)


def stretch(img, d, verb):
    """Посадка/вытягивание. verb в {сутюжить, оттянуть}."""
    _fabric_block(d, 90, 180, 320, 50)
    if verb == "сутюжить":
        # сходящиеся стрелки (сокращение)
        _arrow(d, 120, 150, 220, 180)
        _arrow(d, 380, 150, 280, 180)
        d.text((140, 20), "сутюжить: сократить длину", fill=INK, font=_font(18))
    else:  # оттянуть
        _arrow(d, 220, 180, 120, 210)
        _arrow(d, 280, 180, 380, 210)
        d.text((140, 20), "оттянуть: удлинить край", fill=INK, font=_font(18))
    _iron(d, 250, 300, scale=0.8)


def steam(img, d, verb):
    """Пар. verb в {отпарить, пропарить, декатировать}."""
    _fabric_block(d, 130, 200, 240, 55)
    # облако пара
    for cx, cy in [(200, 130), (250, 100), (300, 130), (250, 150)]:
        d.ellipse([(cx - 40, cy - 30), (cx + 40, cy + 30)], fill=STEAM)
    _iron(d, 250, 60, scale=0.9)
    label = {
        "отпарить": "отпарить: пар без касания",
        "пропарить": "пропарить: обильный пар",
        "декатировать": "декатировать: усадка до раскроя",
    }[verb]
    d.text((140, 300), label, fill=INK, font=_font(18))


# Карта: глагол -> функция отрисовки. Глаголы, не входящие в спец-схемы,
# получают общую схему (flat).
_SPECIAL = {
    "заутюжить": seam,
    "разутьюжить": seam,
    "сутюжить": stretch,
    "оттянуть": stretch,
    "отпарить": steam,
    "пропарить": steam,
    "декатировать": steam,
}


def _font(size: int):
    try:
        from PIL import ImageFont
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


def diagram_path(verb: str) -> Path:
    return IMAGES_DIR / f"{verb}.png"


def generate(verb: str) -> Path:
    """Генерирует PNG-схему для глагола и возвращает путь."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    img, d = _new_canvas()
    draw = _SPECIAL.get(verb, flat)
    draw(img, d, verb)
    path = diagram_path(verb)
    img.save(path)
    return path


def generate_all() -> list[Path]:
    from .content import TERMS
    return [generate(t["verb"]) for t in TERMS]