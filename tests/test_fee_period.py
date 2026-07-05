"""Тесты диапазона дат для истории списаний."""

from datetime import date

from bot.handlers.payments import _fee_period_range


def test_fee_period_current_from_first_day_of_month():
    """Период 'current' — от 1-го числа текущего месяца до сегодня."""
    today = date(2026, 7, 15)
    date_from, date_to = _fee_period_range("current", today)
    assert date_from == date(2026, 7, 1)
    assert date_to == today


def test_fee_period_current_on_first_day():
    """Период 'current' в первый день месяца — диапазон в один день."""
    today = date(2026, 7, 1)
    date_from, date_to = _fee_period_range("current", today)
    assert date_from == date(2026, 7, 1)
    assert date_to == date(2026, 7, 1)


def test_fee_period_last_regular_month():
    """Период 'last' — весь предыдущий календарный месяц."""
    today = date(2026, 7, 15)
    date_from, date_to = _fee_period_range("last", today)
    assert date_from == date(2026, 6, 1)
    assert date_to == date(2026, 6, 30)


def test_fee_period_last_crosses_year_boundary():
    """Период 'last' в январе — переход на декабрь предыдущего года."""
    today = date(2026, 1, 15)
    date_from, date_to = _fee_period_range("last", today)
    assert date_from == date(2025, 12, 1)
    assert date_to == date(2025, 12, 31)

    today_first_day = date(2026, 1, 1)
    date_from, date_to = _fee_period_range("last", today_first_day)
    assert date_from == date(2025, 12, 1)
    assert date_to == date(2025, 12, 31)


def test_fee_period_unknown_falls_back_to_ninety_days():
    """Неизвестный период трактуется как 90-дневное окно ('quarter')."""
    today = date(2026, 7, 15)
    date_from, date_to = _fee_period_range("quarter", today)
    assert date_from == date(2026, 4, 16)
    assert date_to == today

    date_from_unknown, date_to_unknown = _fee_period_range("something-else", today)
    assert date_from_unknown == date_from
    assert date_to_unknown == date_to
