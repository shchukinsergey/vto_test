"""Роутеры хендлеров."""

from . import learn, progress, quiz, start

routers = [start.router, learn.router, quiz.router, progress.router]