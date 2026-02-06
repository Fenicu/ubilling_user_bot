"""Точка входа для запуска бота."""

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent

from bot.config import settings
from bot.db import engine
from bot.handlers import setup_routers
from bot.i18n import LocaleService
from bot.middlewares import AuthMiddleware, LocaleMiddleware
from bot.services import BillingService

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def handle_message_not_modified(event: ErrorEvent) -> bool:
    """
    Глобальный обработчик ошибки 'message is not modified'.

    Игнорирует эту ошибку, так как она безвредна — просто означает,
    что содержимое сообщения не изменилось.
    """
    exc = event.exception
    if isinstance(exc, TelegramBadRequest) and "message is not modified" in str(exc):
        return True
    return False


async def main() -> None:
    """Главная функция запуска бота."""
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    locales_dir = Path(__file__).parent.parent.parent / "locales"
    locale_service = LocaleService(locales_dir, settings.default_locale)
    locale_service.load()
    logger.info("Загружены локали: %s", list(locale_service.available.keys()))

    billing = BillingService(settings.ubilling_url, settings.ubilling_uber_key)
    await billing.start()
    logger.info("BillingService запущен")

    dp["billing"] = billing
    dp["locale_service"] = locale_service

    dp.message.middleware(LocaleMiddleware(locale_service))
    dp.callback_query.middleware(LocaleMiddleware(locale_service))
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    router = setup_routers()
    dp.include_router(router)

    dp.errors.register(handle_message_not_modified, TelegramBadRequest)

    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        await billing.stop()
        await bot.session.close()
        await storage.close()
        await engine.dispose()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
