"""Обработчики команд и событий бота."""

from aiogram import Router

from bot.config import settings
from bot.handlers import (
    announcements,
    credit,
    freeze,
    info,
    language,
    menu,
    payments,
    start,
    support_group,
    support_user,
    tariffs,
    tickets,
)


def setup_routers() -> Router:
    """Создаёт и настраивает главный роутер с подроутерами."""
    router = Router()
    if settings.support_enabled:
        # Групповая сторона идёт первой: у неё собственный фильтр по chat_id
        # (support-группа), поэтому конкурировать с абонентскими хендлерами она не может —
        # но должна успеть перехватить свои апдейты раньше catch-all'а поддержки.
        router.include_router(support_group.router)
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
    if settings.support_enabled:
        router.include_router(support_user.router)
        # Catch-all перехватывает любое сообщение при открытом диалоге — должен идти последним,
        # чтобы не перекрывать более специфичные хендлеры (команды, другие FSM).
        router.include_router(support_user.catchall_router)
    return router
