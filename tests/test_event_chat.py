"""Тесты структурного извлечения чата события aiogram (get_event_chat)."""

from types import SimpleNamespace

from bot.utils.events import get_event_chat


def test_message_event_returns_its_chat():
    """Для Message-подобного события возвращается его chat напрямую."""
    chat = SimpleNamespace(id=1, type="private")
    message = SimpleNamespace(chat=chat)

    assert get_event_chat(message) is chat


def test_callback_query_with_message_returns_message_chat():
    """Для CallbackQuery с message возвращается chat вложенного message."""
    chat = SimpleNamespace(id=-100123, type="supergroup")
    message = SimpleNamespace(chat=chat)
    callback = SimpleNamespace(message=message)

    assert get_event_chat(callback) is chat


def test_callback_query_without_message_returns_none():
    """CallbackQuery без message (например, инлайн-режим) — None."""
    callback = SimpleNamespace(message=None)

    assert get_event_chat(callback) is None


def test_unknown_event_returns_none():
    """Событие без структур chat/message — None."""
    event = SimpleNamespace(foo="bar")

    assert get_event_chat(event) is None
