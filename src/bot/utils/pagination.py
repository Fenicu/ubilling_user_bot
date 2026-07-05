"""Утилиты для пагинации списков."""

from typing import TypeVar

T = TypeVar("T")

PAGE_SIZE = 10


def paginate(items: list[T], page: int, page_size: int = PAGE_SIZE) -> tuple[list[T], int, int]:
    """
    Возвращает элементы для указанной страницы.

    Args:
        items: Полный список элементов
        page: Номер страницы (начиная с 1)
        page_size: Количество элементов на странице

    Returns:
        Кортеж (элементы страницы, зажатый в [1, total_pages] номер страницы, общее количество страниц)
    """
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], page, total_pages


def parse_page_callback(data: str) -> int | None:
    """
    Извлекает число из последнего :-сегмента callback_data.

    Подходит и для `page:section:5`, и для `ticket_view:42` — берётся хвост после последнего ":".

    Returns:
        Число либо None, если хвост нечисловой.
    """
    try:
        return int(data.rsplit(":", 1)[-1])
    except ValueError:
        return None
