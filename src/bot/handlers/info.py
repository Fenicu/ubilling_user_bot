"""Обработчики раздела информации."""

import asyncio
import logging
from typing import Callable

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pydantic import ValidationError

from bot.keyboards.common import back_button
from bot.services import BillingService
from bot.utils.formatting import format_full_user_info

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "info")
async def show_info_menu(callback: CallbackQuery, t: Callable[..., str], **kwargs) -> None:
    """Отображает меню раздела информации."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("info.account_btn"), callback_data="info_account")],
            [InlineKeyboardButton(text=t("info.provider_btn"), callback_data="info_provider")],
            [back_button(t, "menu")],
        ]
    )
    await callback.message.edit_text(t("info.title"), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "info_account")
async def show_account_info(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает полную информацию об аккаунте."""
    try:
        user, services = await asyncio.gather(
            billing.client.get_user_info(login, password_md5),
            billing.client.get_tariff_vservices(login, password_md5),
        )
    except Exception:
        kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "info")]])
        await callback.message.edit_text(t("errors.connection"), reply_markup=kb)
        await callback.answer()
        return

    tariff_name = next((s.tariff_name for s in services if s.is_tariff), None)
    text = format_full_user_info(t, user, tariff_name=tariff_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "info")]])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "info_provider")
async def show_provider_info(
    callback: CallbackQuery,
    t: Callable[..., str],
    billing: BillingService,
    login: str,
    password_md5: str,
    **kwargs,
) -> None:
    """Показывает информацию о провайдере."""
    try:
        agent = await billing.client.get_agent_data(login, password_md5)
    except ValidationError:
        logger.warning("Агент не назначен пользователю login=%s", login)
        kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "info")]])
        await callback.message.edit_text(t("provider.not_assigned"), reply_markup=kb)
        await callback.answer()
        return
    except Exception:
        logger.exception("Ошибка получения данных провайдера для login=%s", login)
        kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "info")]])
        await callback.message.edit_text(t("errors.connection"), reply_markup=kb)
        await callback.answer()
        return

    lines = [
        t("provider.header"),
        "",
        t("provider.name", name=agent.contrname or "—", abbr=agent.agnameabbr or ""),
        t("provider.phone", phone=agent.phone or "—"),
        t("provider.email", email=agent.agmail or "—"),
        t("provider.site", url=agent.siteurl or "—"),
        t("provider.jur_addr", addr=agent.juraddr or "—"),
        t("provider.phys_addr", addr=agent.phisaddr or "—"),
        t("provider.bank", bank=agent.bankname or "—"),
        t("provider.edrpo", edrpo=agent.edrpo or "—"),
        t("provider.license", license=agent.licensenum or "—"),
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=[[back_button(t, "info")]])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()
