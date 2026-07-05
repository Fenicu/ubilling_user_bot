"""Тесты чистых хелперов чата поддержки."""

import html
from dataclasses import dataclass
from datetime import UTC, datetime

from aiogram.types import MessageEntity

from bot.utils.support import (
    autoclose_cutoff,
    build_relay_header,
    build_subscriber_card,
    extract_custom_emoji_ids,
    sanitize_login_hashtag,
)

FAKE_LOCALE = {
    "support_group.card_stub": "🎫 {hashtag}\n👤 Логін: {login} (ID: {telegram_id})\n⚠️ Профіль не знайдено",
    "support_group.card_hashtag": "{hashtag}",
    "support_group.card_realname": "👤 {realname}",
    "support_group.card_balance": "💰 Баланс: {cash} {currency}",
    "support_group.card_tariff": "📋 Тариф: {tariff_name}",
    "support_group.card_status": "📡 Статус: {account_state}",
    "support_group.card_ip": "🌐 IP: {ip}",
    "support_group.relay_header": "{hashtag} · {realname}",
}


def fake_t(key: str, **kwargs) -> str:
    """Мини-заглушка t(), повторяющая экранирование kwargs как в LocaleService.get."""
    template = FAKE_LOCALE[key]
    safe = {k: html.escape(str(v), quote=False) for k, v in kwargs.items()}
    return template.format(**safe)


@dataclass
class FakeUser:
    """Минимальный дубль pyubilling.UserInfo для тестов чистых хелперов."""

    realname: str = ""
    cash: float = 0
    currency: str = "грн"
    account_state: str = ""
    ip: str = ""
    tariff_name: str = ""


class TestSanitizeLoginHashtag:
    """Тесты построения хэштега логина."""

    def test_alnum_login_unchanged_besides_prefix(self):
        """Логин из букв/цифр только получает префикс."""
        assert sanitize_login_hashtag("ivanov77") == "#u_ivanov77"

    def test_special_chars_replaced_with_underscore(self):
        """Дефис и точка заменяются на подчёркивание каждый по отдельности."""
        assert sanitize_login_hashtag("ab-1.c") == "#u_ab_1_c"

    def test_cyrillic_replaced_char_by_char(self):
        """Кириллица заменяется посимвольно, не одним подчёркиванием на всё слово."""
        assert sanitize_login_hashtag("иван") == "#u_" + "_" * 4


class TestBuildRelayHeader:
    """Тесты шапки пересылаемого сообщения."""

    def test_escapes_html_in_realname(self):
        """HTML-теги в ФИО экранируются."""
        result = build_relay_header(fake_t, "ivanov77", "<b>Ivan</b>")

        assert "#u_ivanov77" in result
        assert "&lt;b&gt;Ivan&lt;/b&gt;" in result
        assert "<b>Ivan</b>" not in result

    def test_no_realname_returns_only_hashtag(self):
        """Без ФИО в шапке остаётся только хэштег."""
        result = build_relay_header(fake_t, "ivanov77", None)

        assert result == "#u_ivanov77"


class TestBuildSubscriberCard:
    """Тесты карточки абонента для топика."""

    def test_with_user_contains_hashtag_realname_and_balance(self):
        """При наличии user карточка содержит хэштег, ФИО и баланс."""
        user = FakeUser(realname="Ivan Ivanov", cash=42.5, currency="грн")

        result = build_subscriber_card(fake_t, "ivanov77", 555, user, None)

        assert "#u_ivanov77" in result
        assert "Ivan Ivanov" in result
        assert "42.5 грн" in result

    def test_none_user_gives_stub_with_login_and_telegram_id(self):
        """user=None даёт карточку-заглушку с логином и telegram_id."""
        result = build_subscriber_card(fake_t, "ivanov77", 555, None, None)

        assert "ivanov77" in result
        assert "555" in result

    def test_escapes_html_special_chars_in_user_fields(self):
        """`<` и `&` в полях пользователя экранируются."""
        user = FakeUser(realname="<script>&fun", cash=0, currency="грн")

        result = build_subscriber_card(fake_t, "ivanov77", 555, user, None)

        assert "&lt;script&gt;&amp;fun" in result
        assert "<script>" not in result


class TestExtractCustomEmojiIds:
    """Тесты извлечения кастомных эмодзи из entities/caption_entities."""

    def test_extracts_from_text_and_caption_entities(self):
        """Пары (эмодзи, id) достаются и из text, и из caption одновременно."""
        text = "Hi 😀 there"
        text_entity = MessageEntity(type="custom_emoji", offset=3, length=2, custom_emoji_id="111")
        caption = "Bye 🙂 now"
        caption_entity = MessageEntity(
            type="custom_emoji", offset=4, length=2, custom_emoji_id="222"
        )

        result = extract_custom_emoji_ids(text, [text_entity], caption, [caption_entity])

        assert result == [("😀", "111"), ("🙂", "222")]

    def test_ignores_entities_of_other_types(self):
        """Entities других типов (например bold) в результат не попадают."""
        text = "Hi 😀 there"
        entities = [
            MessageEntity(type="bold", offset=0, length=2),
            MessageEntity(type="custom_emoji", offset=3, length=2, custom_emoji_id="111"),
        ]

        result = extract_custom_emoji_ids(text, entities, None, None)

        assert result == [("😀", "111")]

    def test_empty_input_returns_empty_list(self):
        """Отсутствие текста/entities даёт пустой список."""
        assert extract_custom_emoji_ids(None, None, None, None) == []

    def test_none_entities_with_text_returns_empty_list(self):
        """Текст есть, но entities не переданы — пустой список без падения."""
        assert extract_custom_emoji_ids("Hi 😀 there", None, None, None) == []


class TestAutocloseCutoff:
    """Тесты вычисления порога автозакрытия диалога."""

    def test_subtracts_hours_from_now(self):
        """Порог = now минус заданное число часов."""
        now = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)

        result = autoclose_cutoff(now, 48)

        assert result == datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
