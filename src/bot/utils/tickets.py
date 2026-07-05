"""Хелперы построения треда тикета."""

import html
from datetime import datetime
from typing import Any, Callable

ROOT_TEXT_LIMIT = 2000
SEPARATOR = "\n\n"


def split_threads(tickets: list[Any]) -> dict[int, list[Any]]:
    """Группирует тикеты-ответы по id корневого тикета, сортируя каждую группу по дате."""
    threads: dict[int, list[Any]] = {}
    for ticket in tickets:
        if ticket.reply_id is None:
            continue
        threads.setdefault(ticket.reply_id, []).append(ticket)

    for replies in threads.values():
        replies.sort(key=lambda tk: tk.date)

    return threads


def _format_date(dt: datetime) -> str:
    """Форматирует дату тикета для отображения."""
    return dt.strftime("%Y-%m-%d %H:%M")


def _format_reply(reply: Any) -> str:
    """Форматирует одну запись треда: заголовок с автором + экранированный текст."""
    from_user = html.escape(reply.from_user or "—", quote=False)
    header = f"#{reply.id} · {_format_date(reply.date)} · {from_user}:"
    body = html.escape(reply.text or "", quote=False)
    return f"{header}\n{body}"


def build_ticket_view(
    t: Callable[..., str], root: Any, replies: list[Any], budget: int = 3800
) -> str:
    """
    Строит текст карточки тикета с учётом бюджета символов Telegram.

    Root-текст показывается целиком (не более ROOT_TEXT_LIMIT символов, иначе
    обрезается многоточием). Ответы треда добавляются от новейшего к старейшему,
    пока укладываются в оставшийся бюджет; если тред влез не весь — первой строкой
    треда добавляется отметка о количестве пропущенных ответов.
    """
    status = t("tickets.status_closed") if root.status else t("tickets.status_open")
    root_text_raw = root.text or ""
    root_truncated = len(root_text_raw) > ROOT_TEXT_LIMIT
    root_text = html.escape(root_text_raw[:ROOT_TEXT_LIMIT], quote=False)
    if root_truncated:
        root_text += "…"

    header_text = "\n".join(
        [
            t("tickets.view_header", ticket_id=root.id),
            f"{_format_date(root.date)} · {status}",
            t("tickets.from", from_user=root.from_user or "—"),
            "",
            root_text,
        ]
    )

    if not replies:
        return header_text

    replies_header = t("tickets.replies_header")
    remaining = budget - len(header_text) - len(SEPARATOR) - len(replies_header)

    fitting: list[str] = []
    for reply in reversed(replies):
        entry = _format_reply(reply)
        cost = len(entry) + len(SEPARATOR)
        if cost > remaining:
            break
        fitting.append(entry)
        remaining -= cost

    fitting.reverse()
    truncated_count = len(replies) - len(fitting)

    thread_lines = [replies_header]
    if truncated_count:
        thread_lines.append(t("tickets.thread_truncated", n=truncated_count))
    thread_lines.extend(fitting)

    return header_text + SEPARATOR + SEPARATOR.join(thread_lines)
