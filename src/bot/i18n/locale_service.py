"""Сервис локализации на основе JSON-файлов."""

import json
from pathlib import Path
from typing import Any


class LocaleService:
    """Сервис для работы с локализацией."""

    def __init__(self, locales_dir: Path, default_locale: str = "uk") -> None:
        """
        Инициализация сервиса локализации.

        Args:
            locales_dir: Путь к директории с JSON-файлами локализации
            default_locale: Код локали по умолчанию
        """
        self._locales_dir = locales_dir
        self._default = default_locale
        self._data: dict[str, dict[str, Any]] = {}

    def load(self) -> None:
        """Сканирует locales_dir, загружает все *.json файлы."""
        self._data.clear()
        for path in self._locales_dir.glob("*.json"):
            code = path.stem
            self._data[code] = json.loads(path.read_text("utf-8"))

    @property
    def available(self) -> dict[str, str]:
        """Возвращает {code: display_name} для всех загруженных локалей."""
        return {code: data["_meta"]["name"] for code, data in self._data.items()}

    @property
    def available_with_flags(self) -> dict[str, tuple[str, str]]:
        """Возвращает {code: (name, flag)} для всех загруженных локалей."""
        return {
            code: (data["_meta"]["name"], data["_meta"].get("flag", ""))
            for code, data in self._data.items()
        }

    def get(self, locale: str, key: str, **kwargs: Any) -> str:
        """
        Получить строку по ключу 'section.key', с fallback на default locale.

        Args:
            locale: Код локали
            key: Ключ в формате 'section.subkey'
            **kwargs: Переменные для подстановки в строку

        Returns:
            Локализованная строка с подставленными переменными
        """
        data = self._data.get(locale) or self._data.get(self._default, {})
        parts = key.split(".")
        value: Any = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
                break

        if value is None:
            if locale != self._default:
                return self.get(self._default, key, **kwargs)
            return key

        if kwargs:
            try:
                return str(value).format(**kwargs)
            except KeyError:
                return str(value)

        return str(value)
