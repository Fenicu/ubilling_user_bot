"""Обработчики раздела платежей."""

import html
from datetime import date, timedelta
from typing import Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    fee_period_keyboard,
    pay_card_cancel_keyboard,
    payment_systems_keyboard,
    payments_menu_keyboard,
)
from bot.keyboards.common import pagination_keyboard
from bot.services import BillingService
from bot.states import PayCardForm
from bot.utils.pagination import paginate

router = Router()

FEE_PERIODS = {"current", "last", "quarter"}


def _fee_period_range(period: str, today: date) -> tuple[date, date]:
    """Возвращает диапазон дат для периода списаний."""
    if period == "current":
        return today.replace(day=1), today

    if period == "last":
        first_day = today.replace(day=1)
        date_to = first_day - timedelta(days=1)
        return date_to.replace(day=1), date_to

    return today - timedelta(days=90), today


@router.callback_query(F.data == "payments")
async def show_payments_menu(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Отображает меню раздела платежей."""
    await callback.message.edit_text(t("payments.title"), reply_markup=payments_menu_keyboard(t))
    await callback.answer()


@router.callback_query(F.data == "payments_history")
async def show_payments_history(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает историю платежей."""
    await _show_payments_page(callback, t, billing, login, password_md5, 1)


@router.callback_query(F.data.startswith("page:payments:"))
async def payments_pagination(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обработка пагинации платежей."""
    page = int(callback.data.split(":")[2])
    await _show_payments_page(callback, t, billing, login, password_md5, page)


async def _show_payments_page(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    page: int,
) -> None:
    """Отображает страницу истории платежей."""
    try:
        payments = await billing.client.get_payments(login, password_md5)
        payments = sorted(payments, key=lambda p: p.date or "", reverse=True)
    except Exception:
        await callback.message.edit_text(
            t("errors.connection"),
            reply_markup=payments_menu_keyboard(t),
        )
        await callback.answer()
        return

    if not payments:
        await callback.message.edit_text(
            t("payments.no_history"),
            reply_markup=payments_menu_keyboard(t),
        )
        await callback.answer()
        return

    page_items, total_pages = paginate(payments, page)
    lines = [t("payments.history_title"), ""]
    for p in page_items:
        lines.append(t("payments.payment_line", date=p.date or "—", summ=p.summ, balance=p.balance or "—"))

    kb = pagination_keyboard(t, "payments", page, total_pages, "payments")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "fee_history")
async def show_fee_period_selection(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Показывает выбор периода для списаний."""
    await callback.message.edit_text(t("payments.select_period"), reply_markup=fee_period_keyboard(t))
    await callback.answer()


@router.callback_query(F.data.startswith("fee:"))
async def show_fee_history(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает первую страницу истории списаний за выбранный период."""
    period = callback.data.split(":")[1]
    await _show_fee_page(callback, t, billing, login, password_md5, period, 1)


@router.callback_query(F.data.startswith("page:fee_"))
async def fee_pagination(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обработка пагинации истории списаний."""
    _, section, page_str = callback.data.split(":")
    period = section.removeprefix("fee_")
    await _show_fee_page(callback, t, billing, login, password_md5, period, int(page_str))


async def _show_fee_page(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    period: str,
    page: int,
) -> None:
    """Отображает страницу истории списаний за выбранный период."""
    if period not in FEE_PERIODS:
        period = "quarter"

    date_from, date_to = _fee_period_range(period, date.today())

    try:
        charges = await billing.client.get_fee_charges(
            login, password_md5, date_from=date_from.isoformat(), date_to=date_to.isoformat()
        )
    except Exception:
        await callback.message.edit_text(t("errors.connection"), reply_markup=fee_period_keyboard(t))
        await callback.answer()
        return

    if not charges:
        await callback.message.edit_text(t("payments.no_charges"), reply_markup=fee_period_keyboard(t))
        await callback.answer()
        return

    page_items, total_pages = paginate(charges, page)
    lines = [t("payments.fee_title", date_from=date_from, date_to=date_to), ""]
    for c in page_items:
        lines.append(t("payments.fee_line", date=c.date or "—", fee=c.fee, tariff=c.tariff or "—"))

    kb = pagination_keyboard(t, f"fee_{period}", page, total_pages, "fee_history")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "pay_card")
async def start_pay_card(
    callback: CallbackQuery, state: FSMContext, t: Callable[..., str], **kwargs
) -> None:
    """Начинает процесс активации карты оплаты."""
    await state.set_state(PayCardForm.waiting_card_number)
    await callback.message.edit_text(
        t("payments.enter_card"), reply_markup=pay_card_cancel_keyboard(t)
    )
    await callback.answer()


@router.message(PayCardForm.waiting_card_number, F.text)
async def process_pay_card(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обрабатывает ввод номера карты оплаты."""
    card_number = message.text.strip()
    await state.clear()

    try:
        result = await billing.client.use_pay_card(login, password_md5, card_number)
        text = html.escape(result.message, quote=False) or t("payments.card_result")
    except Exception:
        text = t("errors.connection")

    await message.answer(text, reply_markup=payments_menu_keyboard(t))


@router.callback_query(F.data == "payment_systems")
async def show_payment_systems(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает список платёжных систем."""
    try:
        systems = await billing.client.get_payment_systems(login, password_md5)
        system_list = [(s.name, s.url) for s in systems if s.url]
    except Exception:
        await callback.message.edit_text(t("errors.connection"), reply_markup=payments_menu_keyboard(t))
        await callback.answer()
        return

    if not system_list:
        await callback.message.edit_text(
            t("payments.no_systems"), reply_markup=payments_menu_keyboard(t)
        )
        await callback.answer()
        return

    kb = payment_systems_keyboard(t, system_list)
    await callback.message.edit_text(t("payments.online_title"), reply_markup=kb)
    await callback.answer()
