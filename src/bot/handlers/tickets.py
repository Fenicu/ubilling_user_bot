"""Обработчики раздела тикетов."""

import html
import logging
from typing import Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import ticket_cancel_keyboard, ticket_reply_keyboard, tickets_menu_keyboard
from bot.services import BillingService
from bot.states import TicketForm

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "tickets")
async def show_tickets_menu(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Отображает меню раздела тикетов."""
    await callback.message.edit_text(t("tickets.title"), reply_markup=tickets_menu_keyboard(t))
    await callback.answer()


@router.callback_query(F.data == "tickets_list")
async def show_tickets_list(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает список тикетов."""
    try:
        tickets = await billing.client.get_tickets(login, password_md5)
    except Exception:
        logger.exception("Ошибка получения тикетов для login=%s", login)
        await callback.message.edit_text(
            t("errors.connection"), reply_markup=tickets_menu_keyboard(t)
        )
        await callback.answer()
        return

    if not tickets:
        await callback.message.edit_text(
            t("tickets.no_tickets"), reply_markup=tickets_menu_keyboard(t)
        )
        await callback.answer()
        return

    root_tickets = [tk for tk in tickets if tk.reply_id is None]
    lines = [t("tickets.list_header"), ""]

    for ticket in root_tickets[:5]:
        status = t("tickets.status_open") if not ticket.status else t("tickets.status_closed")
        lines.append(f"🎫 #{ticket.id} ({ticket.date or '—'})")
        lines.append(f"   {status} | {html.escape(ticket.from_user or '—', quote=False)}")
        lines.append(f"   «{html.escape((ticket.text or '')[:50], quote=False)}...»")
        lines.append("")

    kb = tickets_menu_keyboard(t)
    if root_tickets:
        first_ticket = root_tickets[0]
        kb = ticket_reply_keyboard(t, first_ticket.id)

    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "ticket_create")
async def start_ticket_create(
    callback: CallbackQuery, state: FSMContext, t: Callable[..., str], **kwargs
) -> None:
    """Начинает создание нового тикета."""
    await state.set_state(TicketForm.waiting_text)
    await callback.message.edit_text(t("tickets.enter_text"), reply_markup=ticket_cancel_keyboard(t))
    await callback.answer()


@router.message(TicketForm.waiting_text, F.text)
async def process_ticket_text(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обрабатывает текст нового тикета."""
    text = message.text.strip()
    await state.clear()

    try:
        result = await billing.client.create_ticket(login, password_md5, text)
        response = t("tickets.created", ticket_id=result.id) if result.id else t("tickets.create_error")
    except Exception:
        response = t("errors.connection")

    await message.answer(response, reply_markup=tickets_menu_keyboard(t))


@router.callback_query(F.data.startswith("ticket_reply:"))
async def start_ticket_reply(
    callback: CallbackQuery, state: FSMContext, t: Callable[..., str], **kwargs
) -> None:
    """Начинает ответ на тикет."""
    ticket_id = int(callback.data.split(":")[1])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(TicketForm.waiting_reply_text)
    await callback.message.edit_text(
        t("tickets.enter_reply", ticket_id=ticket_id), reply_markup=ticket_cancel_keyboard(t)
    )
    await callback.answer()


@router.message(TicketForm.waiting_reply_text, F.text)
async def process_ticket_reply(
    message: Message,
    state: FSMContext,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обрабатывает текст ответа на тикет."""
    data = await state.get_data()
    ticket_id = data["reply_ticket_id"]
    text = message.text.strip()
    await state.clear()

    try:
        result = await billing.client.create_ticket(login, password_md5, text, reply_id=ticket_id)
        response = t("tickets.reply_sent") if result.id else t("tickets.reply_error")
    except Exception:
        response = t("errors.connection")

    await message.answer(response, reply_markup=tickets_menu_keyboard(t))
