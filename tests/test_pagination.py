"""Тесты пагинации."""

from bot.utils.pagination import paginate


def test_paginate_regular_page():
    """Обычная страница в диапазоне размера."""
    items = list(range(1, 31))
    result, total_pages = paginate(items, page=1, page_size=10)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert total_pages == 3


def test_paginate_last_incomplete_page():
    """Последняя страница с неполным количеством элементов."""
    items = list(range(1, 26))
    result, total_pages = paginate(items, page=3, page_size=10)
    assert result == [21, 22, 23, 24, 25]
    assert total_pages == 3


def test_paginate_page_zero():
    """Номер страницы 0 корректируется на 1."""
    items = list(range(1, 11))
    result, total_pages = paginate(items, page=0, page_size=10)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert total_pages == 1


def test_paginate_page_too_large():
    """Номер страницы больше максимума корректируется на последнюю."""
    items = list(range(1, 26))
    result, total_pages = paginate(items, page=100, page_size=10)
    assert result == [21, 22, 23, 24, 25]
    assert total_pages == 3


def test_paginate_empty_list():
    """Пустой список возвращает пустой результат и 1 страницу."""
    result, total_pages = paginate([], page=1)
    assert result == []
    assert total_pages == 1
