"""Клавиатуры раздела тикетов."""

from typing import Any, Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.common import back_button


def tickets_menu_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт меню раздела тикетов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("tickets.my_tickets"), callback_data="tickets_list")],
            [InlineKeyboardButton(text=t("tickets.create"), callback_data="ticket_create")],
            [back_button(t, "menu")],
        ]
    )


def tickets_list_keyboard(
    t: Callable[..., str], tickets: list[Any], page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру списка тикетов: по кнопке на каждый тикет + пагинация + назад.

    Args:
        t: Функция перевода
        tickets: Тикеты текущей страницы
        page: Текущая страница (начиная с 1)
        total_pages: Общее количество страниц
    """
    rows: list[list[InlineKeyboardButton]] = []
    for ticket in tickets:
        status = t("tickets.status_closed") if ticket.status else t("tickets.status_open")
        date_str = ticket.date.strftime("%Y-%m-%d %H:%M")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🎫 #{ticket.id} · {date_str} · {status}",
                    callback_data=f"ticket_view:{ticket.id}",
                )
            ]
        )

    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 1:
            nav.append(
                InlineKeyboardButton(text="← ", callback_data=f"page:tickets:{page - 1}")
            )
        nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav.append(
                InlineKeyboardButton(text=" →", callback_data=f"page:tickets:{page + 1}")
            )
        rows.append(nav)

    rows.append([back_button(t, "tickets")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def ticket_view_keyboard(t: Callable[..., str], ticket_id: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру карточки тикета: ответить + назад к списку."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("tickets.reply", ticket_id=ticket_id),
                    callback_data=f"ticket_reply:{ticket_id}",
                )
            ],
            [back_button(t, "tickets_list")],
        ]
    )


def ticket_cancel_keyboard(t: Callable[..., str]) -> InlineKeyboardMarkup:
    """Создаёт кнопку отмены для создания/ответа на тикет."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("common.cancel"), callback_data="tickets")]]
    )
