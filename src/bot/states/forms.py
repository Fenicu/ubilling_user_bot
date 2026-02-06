"""FSM состояния для диалогов бота."""

from aiogram.fsm.state import State, StatesGroup


class AuthForm(StatesGroup):
    """Состояния процесса авторизации."""

    waiting_login = State()
    waiting_password = State()


class TicketForm(StatesGroup):
    """Состояния для работы с тикетами."""

    waiting_text = State()
    waiting_reply_text = State()


class PayCardForm(StatesGroup):
    """Состояние для активации карты оплаты."""

    waiting_card_number = State()


class FeeChargeFilter(StatesGroup):
    """Состояния для фильтрации списаний по датам."""

    waiting_date_from = State()
    waiting_date_to = State()
