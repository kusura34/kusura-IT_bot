from aiogram.utils.keyboard import InlineKeyboardBuilder


def contact_keyboard(tg_url: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Написать", url=tg_url)
    kb.button(text="⬅ Назад", callback_data="nav:back:main")
    kb.button(text="🏠 Главное меню", callback_data="nav:home")
    kb.adjust(1)
    return kb.as_markup()
