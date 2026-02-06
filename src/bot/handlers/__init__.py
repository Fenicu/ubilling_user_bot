"""Обработчики команд и событий бота."""

from aiogram import Router

from bot.handlers import (
    announcements,
    credit,
    freeze,
    info,
    language,
    menu,
    payments,
    start,
    tariffs,
    tickets,
)


def setup_routers() -> Router:
    """Создаёт и настраивает главный роутер с подроутерами."""
    router = Router()
    router.include_router(start.router)
    router.include_router(menu.router)
    router.include_router(payments.router)
    router.include_router(tariffs.router)
    router.include_router(tickets.router)
    router.include_router(announcements.router)
    router.include_router(freeze.router)
    router.include_router(credit.router)
    router.include_router(info.router)
    router.include_router(language.router)
    return router
