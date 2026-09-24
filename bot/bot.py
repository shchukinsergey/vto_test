"""Сборка Dispatcher."""

from aiogram import Dispatcher

from .handlers import routers


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    for r in routers:
        dp.include_router(r)
    return dp