"""Обработчики команд и событий бота."""

from aiogram import F, Router

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

    # Абонентская часть работает только в приватных чатах: без этого гейта апдейт из
    # любой группы (support-группа без reply, или чужая группа, куда добавят бота) может
    # провалиться сквозь эти роутеры до HasOpenDialog-catch-all'а поддержки, где матчится
    # по telegram_id без учёта чата. Один фильтр на корневом роутере проверяется до захода
    # в под-роутеры (check_root_filters в aiogram) — точечно чинить каждый хендлер не нужно.
    subscriber_router = Router(name="subscriber")
    subscriber_router.message.filter(F.chat.type == "private")
    subscriber_router.callback_query.filter(F.message.chat.type == "private")

    subscriber_router.include_router(start.router)
    subscriber_router.include_router(menu.router)
    subscriber_router.include_router(payments.router)
    subscriber_router.include_router(tariffs.router)
    subscriber_router.include_router(tickets.router)
    subscriber_router.include_router(announcements.router)
    subscriber_router.include_router(freeze.router)
    subscriber_router.include_router(credit.router)
    subscriber_router.include_router(info.router)
    subscriber_router.include_router(language.router)
    if settings.support_enabled:
        subscriber_router.include_router(support_user.router)
        # Catch-all перехватывает любое сообщение при открытом диалоге — должен идти последним,
        # чтобы не перекрывать более специфичные хендлеры (команды, другие FSM).
        subscriber_router.include_router(support_user.catchall_router)

    router.include_router(subscriber_router)
    return router
