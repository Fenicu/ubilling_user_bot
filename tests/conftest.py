"""Конфигурация pytest для тестов."""

import os

# Устанавливаем обязательные переменные окружения до импорта модулей бота
os.environ.setdefault("BOT_TOKEN", "123:test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@localhost:5432/t")
os.environ.setdefault("UBILLING_URL", "http://localhost")
