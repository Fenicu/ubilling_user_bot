"""Общие элементы клавиатур."""

from typing import Callable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def back_button(t: Callable[..., str], callback_data: str = "menu") -> InlineKeyboardButton:
    """Создаёт кнопку 'Назад'."""
    return InlineKeyboardButton(text=t("menu.back"), callback_data=callback_data)


def pagination_keyboard(
    t: Callable[..., str],
    section: str,
    current_page: int,
    total_pages: int,
    back_callback: str = "menu",
    extra_rows: list[list[InlineKeyboardButton]] | None = None,
) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру с пагинацией.

    Args:
        t: Функция перевода
        section: Секция для callback_data
        current_page: Текущая страница (начиная с 1)
        total_pages: Общее количество страниц
        back_callback: Callback для кнопки назад
        extra_rows: Дополнительные ряды кнопок между пагинацией и кнопкой «Назад»
    """
    rows: list[list[InlineKeyboardButton]] = []

    if total_pages > 1:
        buttons: list[InlineKeyboardButton] = []

        if current_page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text="← ", callback_data=f"page:{section}:{current_page - 1}"
                )
            )

        buttons.append(
            InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop")
        )

        if current_page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text=" →", callback_data=f"page:{section}:{current_page + 1}"
                )
            )

        rows.append(buttons)

    if extra_rows:
        rows.extend(extra_rows)

    rows.append([back_button(t, back_callback)])

    return InlineKeyboardMarkup(inline_keyboard=rows)
