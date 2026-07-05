"""Тесты хелперов построения треда тикета."""

import html
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from bot.utils.tickets import build_ticket_view, split_threads

FAKE_LOCALE = {
    "tickets.view_header": "🎫 Тикет #{ticket_id}",
    "tickets.replies_header": "💬 Ответы:",
    "tickets.thread_truncated": "… показаны не все ответы ({n})",
    "tickets.from": "От: {from_user}",
    "tickets.status_open": "открыт",
    "tickets.status_closed": "закрыт",
    "menu.back": "← Назад",
}


def fake_t(key: str, **kwargs) -> str:
    """Мини-заглушка t(), повторяющая экранирование kwargs как в LocaleService.get."""
    template = FAKE_LOCALE[key]
    safe = {k: html.escape(str(v), quote=False) for k, v in kwargs.items()}
    return template.format(**safe)


@dataclass
class FakeTicket:
    """Минимальный дубль модели Ticket для тестов чистых хелперов."""

    id: int
    date: datetime
    text: str = ""
    status: int = 0
    from_user: str = ""
    reply_id: int | None = None


def make_root(ticket_id: int = 1, **kwargs) -> FakeTicket:
    """Создаёт корневой тикет (reply_id=None)."""
    kwargs.setdefault("date", datetime(2026, 1, 1, 10, 0))
    return FakeTicket(id=ticket_id, reply_id=None, **kwargs)


def make_reply(ticket_id: int, reply_id: int, date: datetime, **kwargs) -> FakeTicket:
    """Создаёт тикет-ответ на другой тикет."""
    return FakeTicket(id=ticket_id, reply_id=reply_id, date=date, **kwargs)


class TestSplitThreads:
    """Тесты группировки тикетов по треду."""

    def test_groups_replies_by_root_id(self):
        """Ответы группируются по id корневого тикета."""
        root1 = make_root(1)
        root2 = make_root(4)
        reply_a = make_reply(2, reply_id=1, date=datetime(2026, 1, 2))
        reply_b = make_reply(3, reply_id=1, date=datetime(2026, 1, 3))
        reply_c = make_reply(5, reply_id=4, date=datetime(2026, 1, 2))

        result = split_threads([root1, reply_a, root2, reply_b, reply_c])

        assert result == {1: [reply_a, reply_b], 4: [reply_c]}

    def test_sorts_replies_by_date_ascending(self):
        """Ответы одного треда сортируются по дате от старых к новым."""
        newer = make_reply(3, reply_id=1, date=datetime(2026, 1, 5))
        older = make_reply(2, reply_id=1, date=datetime(2026, 1, 2))

        result = split_threads([newer, older])

        assert result[1] == [older, newer]

    def test_root_tickets_excluded_from_values(self):
        """Корневые тикеты (reply_id=None) не попадают в результат группировки."""
        root = make_root(1)

        result = split_threads([root])

        assert result == {}

    def test_empty_list_returns_empty_dict(self):
        """Пустой список тикетов даёт пустой словарь."""
        assert split_threads([]) == {}


class TestBuildTicketView:
    """Тесты сборки текста карточки тикета."""

    def test_includes_header_status_date_and_full_text(self):
        """Карточка содержит заголовок, статус, дату, автора и полный текст."""
        root = make_root(7, text="Hello world", from_user="ivan", status=0)

        result = build_ticket_view(fake_t, root, [])

        assert "🎫 Тикет #7" in result
        assert "открыт" in result
        assert "От: ivan" in result
        assert "Hello world" in result
        assert "2026-01-01 10:00" in result

    def test_closed_status_reflected_in_text(self):
        """Truthy-статус тикета отображается как «закрыт»."""
        root = make_root(1, status=1)

        result = build_ticket_view(fake_t, root, [])

        assert "закрыт" in result
        assert "открыт" not in result

    def test_truncates_root_text_over_2000_chars(self):
        """Текст root длиннее 2000 символов обрезается с многоточием."""
        root = make_root(1, text="a" * 2500)

        result = build_ticket_view(fake_t, root, [])

        assert "a" * 2000 + "…" in result
        assert "a" * 2001 not in result

    def test_escapes_html_special_chars_in_root_text(self):
        """Спецсимволы `<` и `&` в тексте root экранируются."""
        root = make_root(1, text="<script>&fun")

        result = build_ticket_view(fake_t, root, [])

        assert "&lt;script&gt;&amp;fun" in result
        assert "<script>" not in result

    def test_includes_all_replies_when_budget_allows(self):
        """При достаточном бюджете в карточке присутствуют все ответы в хронологическом порядке."""
        root = make_root(1, text="root text")
        reply1 = make_reply(2, 1, datetime(2026, 1, 2), text="first reply", from_user="ivan")
        reply2 = make_reply(3, 1, datetime(2026, 1, 3), text="second reply", from_user="petro")

        result = build_ticket_view(fake_t, root, [reply1, reply2])

        assert "💬 Ответы:" in result
        assert result.index("first reply") < result.index("second reply")
        assert "показаны не все ответы" not in result

    def test_escapes_html_special_chars_in_replies(self):
        """Спецсимволы в тексте и имени автора ответа экранируются."""
        root = make_root(1, text="root")
        reply = make_reply(2, 1, datetime(2026, 1, 2), text="<b>hi</b>", from_user="a&b")

        result = build_ticket_view(fake_t, root, [reply])

        assert "&lt;b&gt;hi&lt;/b&gt;" in result
        assert "a&amp;b" in result
        assert "<b>hi</b>" not in result

    def test_truncates_thread_keeping_newest_replies_first(self):
        """Ответы, не влезающие в бюджет, отбрасываются от старых к новым; отметка о пропуске."""
        root = make_root(1, text="root")
        replies = [
            make_reply(2, 1, datetime(2026, 1, 2), text="x" * 100, from_user="a"),
            make_reply(3, 1, datetime(2026, 1, 3), text="y" * 100, from_user="b"),
            make_reply(4, 1, datetime(2026, 1, 4), text="z" * 100, from_user="c"),
        ]

        result = build_ticket_view(fake_t, root, replies, budget=250)

        assert "z" * 100 in result
        assert "y" * 100 not in result
        assert "x" * 100 not in result
        assert "показаны не все ответы (2)" in result

    def test_no_replies_omits_replies_header(self):
        """Без ответов секция «Ответы» не добавляется."""
        root = make_root(1, text="root")

        result = build_ticket_view(fake_t, root, [])

        assert "💬 Ответы:" not in result

    def test_budget_measured_on_escaped_root_text(self):
        """Root из амперсандов: экранирование раздувает x5, карточка всё равно в бюджете."""
        root = make_root(1, text="&" * 2000)

        result = build_ticket_view(fake_t, root, [])

        assert len(result) <= 3800

    def test_truncated_escaped_root_has_no_broken_entity(self):
        """Усечение экранированного root не оставляет обрывок HTML-entity перед многоточием."""
        # 1 + 2000 амперсандов: после экранирования обрезка лимитом попадает внутрь entity
        root = make_root(1, text="x" + "&" * 2000)

        result = build_ticket_view(fake_t, root, [])

        assert result.rstrip().endswith("…")
        body_before_ellipsis = result.rstrip().rsplit("…", 1)[0]
        assert re.search(r"&[a-zA-Z#0-9]*$", body_before_ellipsis) is None

    def test_result_never_exceeds_budget_when_thread_truncated(self):
        """Итоговая карточка не превышает бюджет ни при каком месте усечения треда."""
        root = make_root(1, text="root")
        replies = [
            make_reply(
                i + 2, 1, datetime(2026, 1, 2) + timedelta(days=i), text="r" * 40, from_user="u"
            )
            for i in range(10)
        ]

        header_len = len(build_ticket_view(fake_t, root, []))
        for budget in range(header_len + 45, header_len + 800, 3):
            result = build_ticket_view(fake_t, root, replies, budget=budget)
            assert len(result) <= budget, f"budget={budget}, len={len(result)}"

    def test_none_date_degrades_to_dash(self):
        """Отсутствующая дата root не роняет сборку карточки, показывается прочерк."""
        root = make_root(1, text="root", date=None)

        result = build_ticket_view(fake_t, root, [])

        assert "— · открыт" in result


class TestTicketsListKeyboardDateGuard:
    """Тесты guard'а даты в клавиатуре списка тикетов."""

    def test_none_date_degrades_to_dash_in_button(self):
        """Тикет без даты даёт кнопку с прочерком вместо AttributeError."""
        from bot.keyboards.tickets import tickets_list_keyboard

        ticket = make_root(9, text="root", date=None)

        kb = tickets_list_keyboard(fake_t, [ticket], page=1, total_pages=1)

        assert kb.inline_keyboard[0][0].text == "🎫 #9 · — · открыт"
