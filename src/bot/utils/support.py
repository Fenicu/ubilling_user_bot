"""Чистые хелперы чата поддержки: хэштег логина, карточка абонента, кастомные эмодзи."""

import re
from datetime import datetime, timedelta
from typing import Any, Callable

_HASHTAG_UNSAFE_RE = re.compile(r"[^a-zA-Z0-9_]")


def sanitize_login_hashtag(login: str) -> str:
    """'#u_' + login, где всё вне [a-zA-Z0-9_] заменено на '_' (посимвольно)."""
    return "#u_" + _HASHTAG_UNSAFE_RE.sub("_", login)


def build_relay_header(t: Callable[..., str], login: str, realname: str | None) -> str:
    """Шапка пересылаемого сообщения: '{hashtag} · {realname}', без ФИО — только хэштег."""
    hashtag = sanitize_login_hashtag(login)
    if not realname:
        return hashtag
    return t("support_group.relay_header", hashtag=hashtag, realname=realname)


def build_subscriber_card(
    t: Callable[..., str],
    login: str,
    telegram_id: int,
    user: Any | None,
    tariff_name: str | None,
) -> str:
    """
    Карточка абонента для топика.

    user=None → карточка-заглушка (хэштег, логин, telegram_id). Поля user
    (realname, cash, currency, account_state, ip) подставляются через t() —
    его kwargs экранируются централизованно (см. LocaleService.get), поэтому
    здесь текст полей передаётся как есть, без ручного html.escape.
    """
    hashtag = sanitize_login_hashtag(login)

    if user is None:
        return t(
            "support_group.card_stub",
            hashtag=hashtag,
            login=login,
            telegram_id=telegram_id,
        )

    name = tariff_name or getattr(user, "tariff_name", None) or "—"
    return "\n".join(
        [
            t("support_group.card_hashtag", hashtag=hashtag),
            t("support_group.card_realname", realname=user.realname or "—"),
            t("support_group.card_balance", cash=user.cash, currency=user.currency or "грн"),
            t("support_group.card_tariff", tariff_name=name),
            t("support_group.card_status", account_state=user.account_state or "—"),
            t("support_group.card_ip", ip=user.ip or "—"),
        ]
    )


def extract_custom_emoji_ids(
    text: str | None,
    entities: list[Any] | None,
    caption: str | None,
    caption_entities: list[Any] | None,
) -> list[tuple[str, str]]:
    """
    Пары (эмодзи, custom_emoji_id) из entities и caption_entities типа 'custom_emoji'.

    Эмодзи вырезается срезом text/caption через entity.extract_from(...) —
    метод aiogram, корректно учитывающий UTF-16 offset/length сюррогатных пар.
    """
    result: list[tuple[str, str]] = []
    for source_text, source_entities in ((text, entities), (caption, caption_entities)):
        if not source_text or not source_entities:
            continue
        for entity in source_entities:
            if entity.type != "custom_emoji":
                continue
            emoji = entity.extract_from(source_text)
            result.append((emoji, entity.custom_emoji_id))
    return result


def autoclose_cutoff(now: datetime, hours: int) -> datetime:
    """Порог автозакрытия: now минус hours часов."""
    return now - timedelta(hours=hours)
