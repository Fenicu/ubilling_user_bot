"""Тесты сервиса локализации."""

import json
from pathlib import Path

import pytest

from bot.i18n.locale_service import LocaleService

RU_LOCALE = {
    "_meta": {"name": "Русский"},
    "test": {
        "greeting": "Привет, {name}!",
        "html_template": "<b>{name}</b>",
        "keyerror_case": "Text {missing_placeholder}",
    },
}

UK_LOCALE = {
    "_meta": {"name": "Українська"},
    "test": {
        "only_in_default": "Тільки в дефолті",
    },
}


@pytest.fixture
def locale_service(tmp_path: Path) -> LocaleService:
    """Создаёт LocaleService с временными файлами локалей."""
    (tmp_path / "ru.json").write_text(json.dumps(RU_LOCALE), encoding="utf-8")
    (tmp_path / "uk.json").write_text(json.dumps(UK_LOCALE), encoding="utf-8")
    service = LocaleService(locales_dir=tmp_path, default_locale="uk")
    service.load()
    return service


def test_get_returns_formatted_string_with_regular_substitution(locale_service):
    """Обычная подстановка без спецсимволов возвращает строку как есть."""
    assert locale_service.get("ru", "test.greeting", name="Мир") == "Привет, Мир!"


def test_get_escapes_html_special_chars_in_kwargs(locale_service):
    """Спецсимволы `<`, `>`, `&` в значении экранируются перед подстановкой."""
    result = locale_service.get("ru", "test.greeting", name='<b>&"x"')
    assert result == 'Привет, &lt;b&gt;&amp;"x"!'


def test_get_preserves_template_html_tags_but_escapes_value(locale_service):
    """HTML-теги в самом шаблоне сохраняются, а подставляемое значение экранируется."""
    result = locale_service.get("ru", "test.html_template", name="<script>")
    assert result == "<b>&lt;script&gt;</b>"


def test_get_falls_back_to_default_locale(locale_service):
    """Отсутствующий в запрошенной локали ключ берётся из локали по умолчанию."""
    result = locale_service.get("ru", "test.only_in_default")
    assert result == "Тільки в дефолті"


def test_get_returns_key_when_missing(locale_service):
    """Ключ, отсутствующий во всех локалях, возвращается как есть."""
    result = locale_service.get("ru", "test.nonexistent")
    assert result == "test.nonexistent"


def test_get_returns_unformatted_string_on_format_keyerror(locale_service):
    """При KeyError во время format() возвращается неформатированная строка."""
    result = locale_service.get("ru", "test.keyerror_case", name="ignored")
    assert result == "Text {missing_placeholder}"
