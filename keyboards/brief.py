from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data=f"{prefix}:yes")
    kb.button(text="Нет", callback_data=f"{prefix}:no")
    kb.adjust(2)
    return kb.as_markup()


def project_type_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    types = [
        "Сайт-визитка",
        "Каталог",
        "Интернет-магазин",
        "Маркетплейс",
        "Telegram-бот",
    ]
    for item in types:
        kb.button(text=item, callback_data=f"brief:type:{item}")
    kb.adjust(1)
    return kb.as_markup()


def budget_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="До 300$", callback_data="brief:budget:low")
    kb.button(text="300–1000$", callback_data="brief:budget:mid")
    kb.button(text="1000$+", callback_data="brief:budget:high")
    kb.adjust(1)
    return kb.as_markup()


def post_brief_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Мои работы", callback_data="menu:portfolio")
    kb.button(text="Живая демонстрация", callback_data="menu:demo")
    kb.button(text="Связаться", callback_data="menu:contact")
    kb.adjust(1)
    return kb.as_markup()
