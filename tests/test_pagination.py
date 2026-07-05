"""Тесты пагинации."""

from bot.utils.pagination import paginate, parse_page_callback


def test_paginate_regular_page():
    """Обычная страница в диапазоне размера."""
    items = list(range(1, 31))
    result, page, total_pages = paginate(items, page=1, page_size=10)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert page == 1
    assert total_pages == 3


def test_paginate_last_incomplete_page():
    """Последняя страница с неполным количеством элементов."""
    items = list(range(1, 26))
    result, page, total_pages = paginate(items, page=3, page_size=10)
    assert result == [21, 22, 23, 24, 25]
    assert page == 3
    assert total_pages == 3


def test_paginate_page_zero():
    """Номер страницы 0 корректируется на 1."""
    items = list(range(1, 11))
    result, page, total_pages = paginate(items, page=0, page_size=10)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert page == 1
    assert total_pages == 1


def test_paginate_page_too_large():
    """Номер страницы больше максимума корректируется на последнюю и возвращается зажатым."""
    items = list(range(1, 26))
    result, page, total_pages = paginate(items, page=100, page_size=10)
    assert result == [21, 22, 23, 24, 25]
    assert page == 3
    assert total_pages == 3


def test_paginate_empty_list():
    """Пустой список возвращает пустой результат, страницу 1 и 1 страницу всего."""
    result, page, total_pages = paginate([], page=1)
    assert result == []
    assert page == 1
    assert total_pages == 1


def test_parse_page_callback_valid_number():
    """Числовой последний сегмент callback_data распознаётся."""
    assert parse_page_callback("page:payments:5") == 5


def test_parse_page_callback_non_numeric_segment():
    """Нечисловой последний сегмент даёт None вместо исключения."""
    assert parse_page_callback("page:payments:abc") is None


def test_parse_page_callback_single_id_segment():
    """Работает и для форматов вида ticket_view:{id} / ticket_reply:{id}."""
    assert parse_page_callback("ticket_view:42") == 42
    assert parse_page_callback("ticket_reply:abc") is None
