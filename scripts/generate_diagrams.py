#!/usr/bin/env python3
"""Генерация PNG-схем для всех глаголов ВТО.

Запуск:
    python scripts/generate_diagrams.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import diagrams  # noqa: E402


def main() -> None:
    paths = diagrams.generate_all()
    for p in paths:
        print(f"  ✓ {p}")


if __name__ == "__main__":
    main()