#!/usr/bin/env python3
"""Подбор свободных фото (Openverse) для глаголов ВТО.

Для каждого глагола ищет фото со свободной лицензией (коммерческое
использование + модификация разрешены), скачивает лучший кандидат и
сохраняет как data/images/<verb>.jpg. Если подходящее фото не найдено,
файл не создаётся — остаётся сгенерированная схема (.png).

Запуск:
    python scripts/fetch_images.py
"""
import io
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from bot.db import IMAGES_DIR  # noqa: E402

# Локальный прокси отдаёт самоподписанный сертификат; для скачивания
# публичных картинок проверку SSL отключаем.
_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

API = "https://api.openverse.org/v1/images/"
USER_AGENT = "vto-sewing-bot/0.1 (educational project)"

# Русский глагол -> варианты поисковых запросов (английские).
QUERIES = {
    "утюжить": ["ironing clothes", "ironing shirt", "clothes iron ironing",
                "ironing board iron", "ironing trousers"],
    "отутюжить": ["pressing clothes iron", "ironing garments", "ironing fabric",
                  "ironing dress"],
    "приутюжить": ["pressing seam iron", "pressing fabric with iron",
                   "iron pressing fabric"],
    "заутюжить": ["pressing seam", "seam ironing", "ironing seam clothes"],
    "разутьюжить": ["opening seam iron", "pressing seam open", "ironing seam",
                    "presser foot sewing"],
    "сутюжить": ["tailoring iron", "suit pressing iron", "pressing garment"],
    "оттянуть": ["tailoring pressing", "iron stretching fabric", "ironing wool"],
    "припосадить": ["sewing ease fabric", "tailoring garment", "sewing ironing"],
    "отпарить": ["steam iron", "steaming clothes", "steam ironing"],
    "пропарить": ["steam ironing", "steam pressing fabric", "steam iron clothes"],
    "декатировать": ["fabric steaming", "textile steaming", "fabric iron",
                     "wool ironing"],
    "проутюжить": ["pressing cloth iron", "ironing through cloth",
                   "tailor press cloth", "ironing with cloth"],
}


def search(query: str, limit: int = 20) -> list[dict]:
    params = {
        "q": query,
        "page_size": str(limit),
        "license_type": "commercial,modification",
        "image_type": "photo",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30, context=_SSL) as resp:
        data = json.load(resp)
    return data.get("results", [])


def download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60, context=_SSL) as resp:
        return resp.read()


def to_jpeg(raw: bytes) -> bytes:
    """Конвертирует в JPEG (RGB), обрезая прозрачность/палитру."""
    img = Image.open(io.BytesIO(raw))
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def download_with_retry(url: str, attempts: int = 4) -> bytes:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return download(url)
        except Exception as exc:  # 429/503/таймауты — пробуем ещё с паузой
            last = exc
            time.sleep(2 * (i + 1))
    raise last  # type: ignore[misc]


def pick(results: list[dict]) -> dict | None:
    """Выбирает лучший результат: Wikimedia (Flickr стабильно 503), фото, со ссылкой."""
    # Сначала — только Wikimedia.
    for r in results:
        if r.get("provider") != "wikimedia":
            continue
        if r.get("url") and r.get("image_type", "photo") == "photo":
            return r
    # Запасной вариант — любой провайдер, кроме Flickr.
    for r in results:
        url = r.get("url") or ""
        if not url or "staticflickr" in url or "flickr.com" in url:
            continue
        if r.get("image_type", "photo") == "photo":
            return r
    return None


def fetch_one(verb: str) -> bool:
    for query in QUERIES[verb]:
        try:
            results = search(query)
        except Exception as exc:
            print(f"  {verb}: ошибка запроса «{query}»: {exc}")
            continue
        r = pick(results)
        if not r:
            continue
        # Прямая ссылка на оригинал (миниатюры Openverse падают с 424).
        src = r.get("url")
        try:
            raw = download_with_retry(src)
            jpg = to_jpeg(raw)
        except Exception as exc:
            print(f"  {verb}: не скачалось ({src}): {exc}")
            continue
        out = IMAGES_DIR / f"{verb}.jpg"
        out.write_bytes(jpg)
        print(f"  {verb} ✓ «{r.get('title')}» ({r.get('provider')}, "
              f"{r.get('license')}): {out}")
        return True
    print(f"  {verb}: фото не найдено — остаётся схема")
    return False


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for verb, queries in QUERIES.items():
        if fetch_one(verb):
            ok += 1
    print(f"\nГотово: фото для {ok}/{len(QUERIES)} глаголов.")


if __name__ == "__main__":
    main()