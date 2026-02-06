"""Middleware модули."""

from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.i18n import LocaleMiddleware

__all__ = ["AuthMiddleware", "LocaleMiddleware"]
