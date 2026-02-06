"""Утилиты для форматирования сообщений."""

from typing import Any, Callable


def format_user_info(t: Callable[..., str], user: Any, tariff_name: str | None = None) -> str:
    """
    Форматирует краткую информацию о пользователе для главного меню.

    Args:
        t: Функция перевода
        user: Объект UserInfo из pyubilling
        tariff_name: Название тарифа (переопределяет user.tariff_name)
    """
    name = tariff_name or user.tariff_name or "—"
    return "\n".join(
        [
            t("user_info.header", realname=user.realname or "—"),
            t("user_info.balance", cash=user.cash, currency=user.currency or "грн"),
            t("user_info.tariff", tariff_name=name),
            t("user_info.status", account_state=user.account_state or "—"),
        ]
    )


def format_full_user_info(t: Callable[..., str], user: Any, tariff_name: str | None = None) -> str:
    """
    Форматирует полную карточку информации о пользователе.

    Args:
        t: Функция перевода
        user: Объект UserInfo из pyubilling
        tariff_name: Название тарифа (переопределяет user.tariff_name)
    """
    name = tariff_name or user.tariff_name or "—"
    lines = [
        t("info.header"),
        "",
        t("info.realname", realname=user.realname or "—"),
        t("info.address", address=user.address or "—"),
        t("info.phone", phone=user.phone or "—"),
        t("info.mobile", mobile=user.mobile or "—"),
        t("info.email", email=user.email or "—"),
        t("info.contract", contract=user.contract or "—"),
        t("info.pay_id", pay_id=user.pay_id or "—"),
        "",
        t("info.tariff", tariff_name=name),
        t("info.balance", cash=user.cash, currency=user.currency or "грн"),
        t("info.credit", credit=user.credit or 0, credit_expire=user.credit_expire or "—"),
        t("info.status", account_state=user.account_state or "—"),
        t("info.expire", account_expire=user.account_expire or "—"),
        "",
        t("info.ip", ip=user.ip or "—"),
        t("info.download", traffic_download=user.traffic_download or "0"),
        t("info.upload", traffic_upload=user.traffic_upload or "0"),
        t("info.total", traffic_total=user.traffic_total or "0"),
    ]
    return "\n".join(lines)
