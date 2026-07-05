"""Обработчики раздела тикетов."""

import logging
from typing import Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    ticket_cancel_keyboard,
    ticket_view_keyboard,
    tickets_list_keyboard,
    tickets_menu_keyboard,
)
from bot.services import BillingService
from bot.states import TicketForm
from bot.utils.pagination import paginate, parse_page_callback
from bot.utils.tickets import build_ticket_view, split_threads

logger = logging.getLogger(__name__)
router = Router()

TICKETS_PAGE_SIZE = 5


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
    """Показывает первую страницу списка тикетов."""
    await _render_tickets_list(callback, t, billing, login, password_md5, 1)
    await callback.answer()


@router.callback_query(F.data.startswith("page:tickets:"))
async def tickets_pagination(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Обработка пагинации списка тикетов."""
    page = parse_page_callback(callback.data)
    if page is None:
        await callback.answer()
        return
    await _render_tickets_list(callback, t, billing, login, password_md5, page)
    await callback.answer()


async def _render_tickets_list(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    page: int,
    tickets: list | None = None,
) -> None:
    """Рендерит страницу списка корневых тикетов; tickets — уже загруженный список, если есть."""
    if tickets is None:
        try:
            tickets = await billing.client.get_tickets(login, password_md5)
        except Exception:
            logger.exception("Ошибка получения тикетов для login=%s", login)
            await callback.message.edit_text(
                t("errors.connection"), reply_markup=tickets_menu_keyboard(t)
            )
            return

    root_tickets = [tk for tk in tickets if tk.reply_id is None]
    if not root_tickets:
        await callback.message.edit_text(
            t("tickets.no_tickets"), reply_markup=tickets_menu_keyboard(t)
        )
        return

    page_items, page, total_pages = paginate(root_tickets, page, page_size=TICKETS_PAGE_SIZE)
    kb = tickets_list_keyboard(t, page_items, page, total_pages)
    await callback.message.edit_text(t("tickets.list_hint"), reply_markup=kb)


@router.callback_query(F.data.startswith("ticket_view:"))
async def show_ticket_view(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает карточку тикета с треда ответов."""
    ticket_id = parse_page_callback(callback.data)
    if ticket_id is None:
        await callback.answer()
        return

    try:
        tickets = await billing.client.get_tickets(login, password_md5)
    except Exception:
        logger.exception("Ошибка получения тикетов для login=%s", login)
        await callback.message.edit_text(
            t("errors.connection"), reply_markup=tickets_menu_keyboard(t)
        )
        await callback.answer()
        return

    root = next((tk for tk in tickets if tk.id == ticket_id and tk.reply_id is None), None)
    if root is None:
        await callback.answer(t("tickets.not_found"), show_alert=True)
        await _render_tickets_list(callback, t, billing, login, password_md5, 1, tickets=tickets)
        return

    replies = split_threads(tickets).get(ticket_id, [])
    text = build_ticket_view(t, root, replies)

    await callback.message.edit_text(text, reply_markup=ticket_view_keyboard(t, ticket_id))
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
    ticket_id = parse_page_callback(callback.data)
    if ticket_id is None:
        await callback.answer()
        return
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
